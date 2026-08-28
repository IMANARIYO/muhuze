import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import storage
from app.modules.auth.repository import AccountRepository, AuthorizationRepository
from app.modules.premium.models import (
    PremiumPlan,
    SellerSubscription,
    SubscriptionStatus,
)
from app.modules.premium.repository import (
    PremiumPlanRepository,
    SellerSubscriptionRepository,
)
from app.modules.premium.service import BASIC_COMMISSION_RATE


def unique_email() -> str:
    return f"premium-test-{uuid.uuid4().hex}@example.com"


def unique_business_name() -> str:
    return f"Business {uuid.uuid4().hex}"


def auth_headers(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def register_and_login(
    client: AsyncClient, password: str = "supersecret123"
) -> tuple[str, dict]:
    email = unique_email()
    await client.post(
        "/api/v1/auth/register", json={"email": email, "password": password}
    )
    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    return email, response.json()["data"]


async def make_admin(client: AsyncClient, db: AsyncSession) -> dict:
    email, tokens = await register_and_login(client)
    account = await AccountRepository(db).get_by_email(email)
    assert account is not None
    admin_role = await AuthorizationRepository(db).get_role_by_name("admin")
    assert admin_role is not None
    await AuthorizationRepository(db).assign_role(
        account_id=account.id, role_id=admin_role.id
    )
    await db.commit()
    return tokens


def fake_upload(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_do_upload(file_obj, *, folder, public_id, delivery_type):
        return {
            "public_id": public_id,
            "url": f"http://res.cloudinary.com/{public_id}",
            "secure_url": f"https://res.cloudinary.com/{public_id}",
            "format": "jpg",
            "resource_type": "image",
            "type": delivery_type,
            "bytes": 1234,
        }

    monkeypatch.setattr(storage, "_do_upload", _fake_do_upload)
    monkeypatch.setattr(storage, "_do_delete", lambda *a, **k: None)


@pytest.fixture(autouse=True)
def _cloudinary_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(storage.settings, "cloudinary_cloud_name", "test-cloud")
    monkeypatch.setattr(storage.settings, "cloudinary_api_key", "test-key")
    monkeypatch.setattr(storage.settings, "cloudinary_api_secret", "test-secret")


async def make_active_seller(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    db: AsyncSession,
) -> dict:
    """Registers a seller account and drives it through the approval flow so
    it ends up `active` — the state `get_current_seller` requires."""
    _, seller_tokens = await register_and_login(client)
    headers = auth_headers(seller_tokens)

    await client.post(
        "/api/v1/sellers",
        json={"business_name": unique_business_name()},
        headers=headers,
    )
    fake_upload(monkeypatch)
    for doc_type in ("national_id_front", "national_id_back"):
        await client.post(
            "/api/v1/sellers/me/documents",
            data={"document_type": doc_type},
            files={"file": ("id.jpg", b"fake-bytes", "image/jpeg")},
            headers=headers,
        )
    await client.post("/api/v1/sellers/me/submit", headers=headers)

    my_seller = await client.get("/api/v1/sellers/me", headers=headers)
    seller_id = my_seller.json()["data"]["id"]

    admin_tokens = await make_admin(client, db)
    await client.post(
        f"/api/v1/sellers/{seller_id}/approve", headers=auth_headers(admin_tokens)
    )
    return headers


async def make_plan(db: AsyncSession, *, code: str | None = None) -> PremiumPlan:
    plan = PremiumPlan(
        code=code or f"tp-{uuid.uuid4().hex[:12]}",
        name="Test Premium",
        price=10,
        currency="USD",
        duration_days=30,
        commission_rate=7,
        is_active=True,
    )
    created = await PremiumPlanRepository(db).create(plan=plan)
    await db.commit()
    return created


async def get_active_seller_id(client: AsyncClient, headers: dict) -> uuid.UUID:
    my_seller = await client.get("/api/v1/sellers/me", headers=headers)
    return my_seller.json()["data"]["id"]


# --- plan listing & admin CRUD ----------------------------------------


async def test_plans_public_list_needs_no_auth(
    client: AsyncClient, db: AsyncSession
) -> None:
    await make_plan(db, code=f"plan-{uuid.uuid4().hex}")
    response = await client.get("/api/v1/premium/plans")
    assert response.status_code == 200
    plans = response.json()["data"]
    assert len(plans) >= 1
    assert plans[0]["commission_rate"] == 7


async def test_non_admin_cannot_create_plan(
    client: AsyncClient, db: AsyncSession
) -> None:
    await make_admin(client, db)
    _, tokens = await register_and_login(client)
    response = await client.post(
        "/api/v1/premium/plans",
        json={
            "code": "x",
            "name": "X",
            "price": 10,
            "duration_days": 30,
            "commission_rate": 7,
        },
        headers=auth_headers(tokens),
    )
    assert response.status_code == 403


async def test_admin_can_create_plan(
    client: AsyncClient, db: AsyncSession
) -> None:
    admin_tokens = await make_admin(client, db)
    response = await client.post(
        "/api/v1/premium/plans",
        json={
            "code": f"ap-{uuid.uuid4().hex[:12]}",
            "name": "Admin Plan",
            "price": 10,
            "duration_days": 30,
            "commission_rate": 7,
        },
        headers=auth_headers(admin_tokens),
    )
    assert response.status_code == 201
    assert response.json()["data"]["commission_rate"] == 7


# --- subscribe / status / commission resolution -----------------------


async def test_basic_seller_has_12_percent_rate(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    headers = await make_active_seller(client, monkeypatch, db)
    response = await client.get("/api/v1/premium/me", headers=headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["is_premium"] is False
    assert data["commission_rate"] == BASIC_COMMISSION_RATE
    assert data["subscription"] is None


async def test_subscribe_makes_seller_premium_at_7_percent(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    headers = await make_active_seller(client, monkeypatch, db)
    plan = await make_plan(db)

    subscribe = await client.post(
        "/api/v1/premium/subscribe",
        json={"plan_id": str(plan.id)},
        headers=headers,
    )
    assert subscribe.status_code == 201

    me = await client.get("/api/v1/premium/me", headers=headers)
    data = me.json()["data"]
    assert data["is_premium"] is True
    assert data["commission_rate"] == 7
    assert data["subscription"]["plan_id"] == str(plan.id)


async def test_subscribe_requires_active_seller(
    client: AsyncClient, db: AsyncSession
) -> None:
    plan = await make_plan(db)
    _, tokens = await register_and_login(client)
    await client.post(
        "/api/v1/sellers",
        json={"business_name": unique_business_name()},
        headers=auth_headers(tokens),
    )
    response = await client.post(
        "/api/v1/premium/subscribe",
        json={"plan_id": str(plan.id)},
        headers=auth_headers(tokens),
    )
    assert response.status_code == 409


async def test_subscribe_to_retired_plan_is_409(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    headers = await make_active_seller(client, monkeypatch, db)
    plan = await make_plan(db)
    plan.is_active = False
    await db.commit()

    response = await client.post(
        "/api/v1/premium/subscribe",
        json={"plan_id": str(plan.id)},
        headers=headers,
    )
    assert response.status_code == 409


async def test_buying_new_plan_expires_the_previous(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    headers = await make_active_seller(client, monkeypatch, db)
    plan_a = await make_plan(db, code=f"a-{uuid.uuid4().hex}")
    plan_b = await make_plan(db, code=f"b-{uuid.uuid4().hex}")

    await client.post(
        "/api/v1/premium/subscribe",
        json={"plan_id": str(plan_a.id)},
        headers=headers,
    )
    await client.post(
        "/api/v1/premium/subscribe",
        json={"plan_id": str(plan_b.id)},
        headers=headers,
    )

    history = await client.get("/api/v1/premium/me/history", headers=headers)
    statuses = {
        item["status"] for item in history.json()["data"]
    }
    assert statuses == {"active", "expired"}


async def test_cancel_drops_seller_back_to_basic(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    headers = await make_active_seller(client, monkeypatch, db)
    plan = await make_plan(db)
    await client.post(
        "/api/v1/premium/subscribe",
        json={"plan_id": str(plan.id)},
        headers=headers,
    )

    cancel = await client.post("/api/v1/premium/me/cancel", headers=headers)
    assert cancel.status_code == 200
    assert cancel.json()["data"]["status"] == "cancelled"

    me = await client.get("/api/v1/premium/me", headers=headers)
    data = me.json()["data"]
    assert data["is_premium"] is False
    assert data["commission_rate"] == BASIC_COMMISSION_RATE
    assert data["subscription"] is None


async def test_cancel_without_subscription_is_404(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    headers = await make_active_seller(client, monkeypatch, db)
    response = await client.post("/api/v1/premium/me/cancel", headers=headers)
    assert response.status_code == 404


async def test_expired_subscription_counts_as_basic(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    headers = await make_active_seller(client, monkeypatch, db)
    seller_id = uuid.UUID(await get_active_seller_id(client, headers))
    plan = await make_plan(db)
    past = datetime.now(UTC) - timedelta(days=10)

    subscription = SellerSubscription(
        seller_id=seller_id,
        plan_id=plan.id,
        status=SubscriptionStatus.ACTIVE,
        commission_rate=7,
        starts_at=past - timedelta(days=30),
        expires_at=past,
    )
    repo = SellerSubscriptionRepository(db)
    db.add(subscription)
    await db.commit()

    me = await client.get("/api/v1/premium/me", headers=headers)
    data = me.json()["data"]
    assert data["is_premium"] is False
    assert data["commission_rate"] == BASIC_COMMISSION_RATE

    # The stale `active` row was lazily flipped to `expired`. The request ran
    # on a separate session (`get_db`), so drop the test session's cached,
    # identity-mapped copy first, otherwise the re-read returns the old
    # `active` object and misses the change.
    db.expunge(subscription)
    refreshed = await repo.get_by_id(subscription.id)
    assert refreshed is not None
    assert refreshed.status == SubscriptionStatus.EXPIRED
