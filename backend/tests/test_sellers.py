import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import storage
from app.modules.auth.repository import AccountRepository, AuthorizationRepository


def unique_email() -> str:
    return f"seller-test-{uuid.uuid4().hex}@example.com"


def unique_business_name() -> str:
    return f"Business {uuid.uuid4().hex}"


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


def auth_headers(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def fake_upload(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every seller test that touches document upload needs Cloudinary
    faked out — real network calls are never acceptable in tests."""

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


async def upload_national_id(
    client: AsyncClient, headers: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_upload(monkeypatch)
    for doc_type in ("national_id_front", "national_id_back"):
        await client.post(
            "/api/v1/sellers/me/documents",
            data={"document_type": doc_type},
            files={"file": ("id.jpg", b"fake-bytes", "image/jpeg")},
            headers=headers,
        )


# --- registration ------------------------------------------------------


async def test_register_requires_auth(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/sellers", json={"business_name": unique_business_name()}
    )
    assert response.status_code == 401


async def test_register_creates_draft_seller(client: AsyncClient) -> None:
    _, tokens = await register_and_login(client)
    name = unique_business_name()
    response = await client.post(
        "/api/v1/sellers", json={"business_name": name}, headers=auth_headers(tokens)
    )
    assert response.status_code == 201
    body = response.json()["data"]
    assert body["status"] == "draft"
    assert body["business_name"] == name


async def test_register_twice_is_409(client: AsyncClient) -> None:
    _, tokens = await register_and_login(client)
    headers = auth_headers(tokens)
    await client.post(
        "/api/v1/sellers",
        json={"business_name": unique_business_name()},
        headers=headers,
    )

    response = await client.post(
        "/api/v1/sellers",
        json={"business_name": unique_business_name()},
        headers=headers,
    )
    assert response.status_code == 409


async def test_register_duplicate_business_name_is_409(client: AsyncClient) -> None:
    name = unique_business_name()
    _, tokens_a = await register_and_login(client)
    await client.post(
        "/api/v1/sellers", json={"business_name": name}, headers=auth_headers(tokens_a)
    )

    _, tokens_b = await register_and_login(client)
    response = await client.post(
        "/api/v1/sellers", json={"business_name": name}, headers=auth_headers(tokens_b)
    )
    assert response.status_code == 409


async def test_get_my_seller_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/sellers/me")
    assert response.status_code == 401


async def test_get_my_seller_404_before_registration(client: AsyncClient) -> None:
    _, tokens = await register_and_login(client)
    response = await client.get("/api/v1/sellers/me", headers=auth_headers(tokens))
    assert response.status_code == 404


# --- editing while draft/rejected ---------------------------------------


async def test_update_profile_while_draft_succeeds(client: AsyncClient) -> None:
    _, tokens = await register_and_login(client)
    headers = auth_headers(tokens)
    await client.post(
        "/api/v1/sellers",
        json={"business_name": unique_business_name()},
        headers=headers,
    )

    new_name = unique_business_name()
    response = await client.patch(
        "/api/v1/sellers/me",
        json={"business_name": new_name, "business_description": "We sell things"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["business_name"] == new_name


# --- submission ----------------------------------------------------------


async def test_submit_without_documents_is_422(client: AsyncClient) -> None:
    _, tokens = await register_and_login(client)
    headers = auth_headers(tokens)
    await client.post(
        "/api/v1/sellers",
        json={"business_name": unique_business_name()},
        headers=headers,
    )

    response = await client.post("/api/v1/sellers/me/submit", headers=headers)
    assert response.status_code == 422


async def test_submit_with_required_documents_succeeds_and_sends_email(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch, captured_emails: list[dict]
) -> None:
    email, tokens = await register_and_login(client)
    headers = auth_headers(tokens)
    await client.post(
        "/api/v1/sellers",
        json={"business_name": unique_business_name()},
        headers=headers,
    )
    await upload_national_id(client, headers, monkeypatch)

    response = await client.post("/api/v1/sellers/me/submit", headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "pending_review"
    assert any(e["to"] == email for e in captured_emails)


async def test_submit_twice_is_409(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch, captured_emails: list[dict]
) -> None:
    _, tokens = await register_and_login(client)
    headers = auth_headers(tokens)
    await client.post(
        "/api/v1/sellers",
        json={"business_name": unique_business_name()},
        headers=headers,
    )
    await upload_national_id(client, headers, monkeypatch)
    await client.post("/api/v1/sellers/me/submit", headers=headers)

    response = await client.post("/api/v1/sellers/me/submit", headers=headers)
    assert response.status_code == 409


async def test_cannot_edit_profile_while_pending_review(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch, captured_emails: list[dict]
) -> None:
    _, tokens = await register_and_login(client)
    headers = auth_headers(tokens)
    await client.post(
        "/api/v1/sellers",
        json={"business_name": unique_business_name()},
        headers=headers,
    )
    await upload_national_id(client, headers, monkeypatch)
    await client.post("/api/v1/sellers/me/submit", headers=headers)

    response = await client.patch(
        "/api/v1/sellers/me",
        json={"business_name": unique_business_name()},
        headers=headers,
    )
    assert response.status_code == 409


# --- admin: list / get ----------------------------------------------------


async def test_non_admin_cannot_list_sellers(client: AsyncClient) -> None:
    _, tokens = await register_and_login(client)
    response = await client.get("/api/v1/sellers", headers=auth_headers(tokens))
    assert response.status_code == 403


async def test_admin_can_list_sellers_filtered_by_status(
    client: AsyncClient,
    db: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
    captured_emails: list[dict],
) -> None:
    admin_tokens = await make_admin(client, db)
    _, seller_tokens = await register_and_login(client)
    headers = auth_headers(seller_tokens)
    name = unique_business_name()
    await client.post("/api/v1/sellers", json={"business_name": name}, headers=headers)
    await upload_national_id(client, headers, monkeypatch)
    await client.post("/api/v1/sellers/me/submit", headers=headers)

    response = await client.get(
        "/api/v1/sellers?status=pending_review", headers=auth_headers(admin_tokens)
    )
    assert response.status_code == 200
    names = {s["business_name"] for s in response.json()["data"]}
    assert name in names


async def test_get_unknown_seller_is_404(client: AsyncClient, db: AsyncSession) -> None:
    admin_tokens = await make_admin(client, db)
    response = await client.get(
        f"/api/v1/sellers/{uuid.uuid4()}", headers=auth_headers(admin_tokens)
    )
    assert response.status_code == 404


# --- admin: approve / reject ------------------------------------------


async def test_non_admin_cannot_approve(client: AsyncClient) -> None:
    _, tokens = await register_and_login(client)
    response = await client.post(
        f"/api/v1/sellers/{uuid.uuid4()}/approve", headers=auth_headers(tokens)
    )
    assert response.status_code == 403


async def test_approve_when_not_pending_is_409(
    client: AsyncClient, db: AsyncSession
) -> None:
    admin_tokens = await make_admin(client, db)
    _, seller_tokens = await register_and_login(client)
    await client.post(
        "/api/v1/sellers",
        json={"business_name": unique_business_name()},
        headers=auth_headers(seller_tokens),
    )
    my_seller = await client.get(
        "/api/v1/sellers/me", headers=auth_headers(seller_tokens)
    )
    seller_id = my_seller.json()["data"]["id"]

    response = await client.post(
        f"/api/v1/sellers/{seller_id}/approve", headers=auth_headers(admin_tokens)
    )
    assert response.status_code == 409


async def test_full_approval_flow_grants_seller_role_and_keeps_account_active(
    client: AsyncClient,
    db: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
    captured_emails: list[dict],
) -> None:
    admin_tokens = await make_admin(client, db)
    admin_headers = auth_headers(admin_tokens)
    seller_email, seller_tokens = await register_and_login(client)
    seller_headers = auth_headers(seller_tokens)

    await client.post(
        "/api/v1/sellers",
        json={"business_name": unique_business_name()},
        headers=seller_headers,
    )
    await upload_national_id(client, seller_headers, monkeypatch)
    await client.post("/api/v1/sellers/me/submit", headers=seller_headers)

    my_seller = await client.get("/api/v1/sellers/me", headers=seller_headers)
    seller_id = my_seller.json()["data"]["id"]

    captured_emails.clear()
    approve_response = await client.post(
        f"/api/v1/sellers/{seller_id}/approve", headers=admin_headers
    )
    assert approve_response.status_code == 200
    assert approve_response.json()["data"]["status"] == "active"
    assert any(e["to"] == seller_email for e in captured_emails)

    authz = await client.get("/api/v1/auth/me/authorization", headers=seller_headers)
    assert sorted(authz.json()["data"]["roles"]) == ["buyer", "seller"]

    # Account itself is untouched by seller approval — still able to log in.
    login_again = await client.post(
        "/api/v1/auth/login", json={"email": seller_email, "password": "supersecret123"}
    )
    assert login_again.status_code == 200


async def test_admin_can_reject_seller_with_reason_and_role_is_not_granted(
    client: AsyncClient,
    db: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
    captured_emails: list[dict],
) -> None:
    admin_tokens = await make_admin(client, db)
    admin_headers = auth_headers(admin_tokens)
    seller_email, seller_tokens = await register_and_login(client)
    seller_headers = auth_headers(seller_tokens)

    await client.post(
        "/api/v1/sellers",
        json={"business_name": unique_business_name()},
        headers=seller_headers,
    )
    await upload_national_id(client, seller_headers, monkeypatch)
    await client.post("/api/v1/sellers/me/submit", headers=seller_headers)
    seller_id = (await client.get("/api/v1/sellers/me", headers=seller_headers)).json()[
        "data"
    ]["id"]

    captured_emails.clear()
    response = await client.post(
        f"/api/v1/sellers/{seller_id}/reject",
        json={"reason": "Documents are unreadable"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["status"] == "rejected"
    assert body["rejection_reason"] == "Documents are unreadable"
    assert any(e["to"] == seller_email for e in captured_emails)

    authz = await client.get("/api/v1/auth/me/authorization", headers=seller_headers)
    assert authz.json()["data"]["roles"] == ["buyer"]


async def test_rejected_seller_can_edit_and_resubmit(
    client: AsyncClient,
    db: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
    captured_emails: list[dict],
) -> None:
    admin_tokens = await make_admin(client, db)
    admin_headers = auth_headers(admin_tokens)
    _, seller_tokens = await register_and_login(client)
    seller_headers = auth_headers(seller_tokens)

    await client.post(
        "/api/v1/sellers",
        json={"business_name": unique_business_name()},
        headers=seller_headers,
    )
    await upload_national_id(client, seller_headers, monkeypatch)
    await client.post("/api/v1/sellers/me/submit", headers=seller_headers)
    seller_id = (await client.get("/api/v1/sellers/me", headers=seller_headers)).json()[
        "data"
    ]["id"]
    await client.post(
        f"/api/v1/sellers/{seller_id}/reject",
        json={"reason": "fix it"},
        headers=admin_headers,
    )

    new_name = unique_business_name()
    update_response = await client.patch(
        "/api/v1/sellers/me", json={"business_name": new_name}, headers=seller_headers
    )
    assert update_response.status_code == 200

    resubmit_response = await client.post(
        "/api/v1/sellers/me/submit", headers=seller_headers
    )
    assert resubmit_response.status_code == 200
    assert resubmit_response.json()["data"]["status"] == "pending_review"


# --- admin: suspend / reactivate; self: deactivate ------------------------


async def test_suspend_when_not_active_is_409(
    client: AsyncClient, db: AsyncSession
) -> None:
    admin_tokens = await make_admin(client, db)
    _, seller_tokens = await register_and_login(client)
    await client.post(
        "/api/v1/sellers",
        json={"business_name": unique_business_name()},
        headers=auth_headers(seller_tokens),
    )
    seller_id = (
        await client.get("/api/v1/sellers/me", headers=auth_headers(seller_tokens))
    ).json()["data"]["id"]

    response = await client.post(
        f"/api/v1/sellers/{seller_id}/suspend",
        json={},
        headers=auth_headers(admin_tokens),
    )
    assert response.status_code == 409


async def test_suspend_then_reactivate_active_seller(
    client: AsyncClient,
    db: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
    captured_emails: list[dict],
) -> None:
    admin_tokens = await make_admin(client, db)
    admin_headers = auth_headers(admin_tokens)
    seller_email, seller_tokens = await register_and_login(client)
    seller_headers = auth_headers(seller_tokens)

    await client.post(
        "/api/v1/sellers",
        json={"business_name": unique_business_name()},
        headers=seller_headers,
    )
    await upload_national_id(client, seller_headers, monkeypatch)
    await client.post("/api/v1/sellers/me/submit", headers=seller_headers)
    seller_id = (await client.get("/api/v1/sellers/me", headers=seller_headers)).json()[
        "data"
    ]["id"]
    await client.post(f"/api/v1/sellers/{seller_id}/approve", headers=admin_headers)

    suspend_response = await client.post(
        f"/api/v1/sellers/{seller_id}/suspend",
        json={"reason": "policy violation"},
        headers=admin_headers,
    )
    assert suspend_response.status_code == 200
    assert suspend_response.json()["data"]["status"] == "suspended"

    # The account itself is unaffected by suspension.
    login_again = await client.post(
        "/api/v1/auth/login", json={"email": seller_email, "password": "supersecret123"}
    )
    assert login_again.status_code == 200

    reactivate_response = await client.post(
        f"/api/v1/sellers/{seller_id}/reactivate", headers=admin_headers
    )
    assert reactivate_response.status_code == 200
    assert reactivate_response.json()["data"]["status"] == "active"


async def test_reactivate_when_not_suspended_is_409(
    client: AsyncClient, db: AsyncSession
) -> None:
    admin_tokens = await make_admin(client, db)
    _, seller_tokens = await register_and_login(client)
    await client.post(
        "/api/v1/sellers",
        json={"business_name": unique_business_name()},
        headers=auth_headers(seller_tokens),
    )
    seller_id = (
        await client.get("/api/v1/sellers/me", headers=auth_headers(seller_tokens))
    ).json()["data"]["id"]

    response = await client.post(
        f"/api/v1/sellers/{seller_id}/reactivate", headers=auth_headers(admin_tokens)
    )
    assert response.status_code == 409


async def test_deactivate_requires_active_status(client: AsyncClient) -> None:
    _, tokens = await register_and_login(client)
    headers = auth_headers(tokens)
    await client.post(
        "/api/v1/sellers",
        json={"business_name": unique_business_name()},
        headers=headers,
    )

    response = await client.post("/api/v1/sellers/me/deactivate", headers=headers)
    assert response.status_code == 409


async def test_seller_can_deactivate_own_active_account(
    client: AsyncClient,
    db: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
    captured_emails: list[dict],
) -> None:
    admin_tokens = await make_admin(client, db)
    admin_headers = auth_headers(admin_tokens)
    _, seller_tokens = await register_and_login(client)
    seller_headers = auth_headers(seller_tokens)

    await client.post(
        "/api/v1/sellers",
        json={"business_name": unique_business_name()},
        headers=seller_headers,
    )
    await upload_national_id(client, seller_headers, monkeypatch)
    await client.post("/api/v1/sellers/me/submit", headers=seller_headers)
    seller_id = (await client.get("/api/v1/sellers/me", headers=seller_headers)).json()[
        "data"
    ]["id"]
    await client.post(f"/api/v1/sellers/{seller_id}/approve", headers=admin_headers)

    response = await client.post(
        "/api/v1/sellers/me/deactivate", headers=seller_headers
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "deactivated"
