import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import storage
from app.modules.auth.repository import AccountRepository, AuthorizationRepository
from app.modules.premium.models import PremiumPlan
from app.modules.premium.repository import PremiumPlanRepository

"""End-to-end commerce tests: cart -> checkout -> payment -> revenue, using
controlled numbers so the money math is verifiable:

    Seller gross 100.00 @ 12% (basic) -> MUHUZE 12.00, seller 88.00
    Seller gross 100.00 @  7% (premium) -> MUHUZE  7.00, seller 93.00
"""


# ── helpers (mirror test_catalog / test_premium) ────────────────────────


def unique_email() -> str:
    return f"commerce-test-{uuid.uuid4().hex}@example.com"


def unique_name(prefix: str = "Thing") -> str:
    return f"{prefix} {uuid.uuid4().hex}"


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
    monkeypatch.setattr(
        storage, "_do_get_public_url", lambda public_id, **k: f"https://cdn/{public_id}"
    )


@pytest.fixture(autouse=True)
def _cloudinary_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(storage.settings, "cloudinary_cloud_name", "test-cloud")
    monkeypatch.setattr(storage.settings, "cloudinary_api_key", "test-key")
    monkeypatch.setattr(storage.settings, "cloudinary_api_secret", "test-secret")


async def make_active_seller(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> tuple[dict, str]:
    """Registers an account, becomes an active seller, returns
    (tokens, seller_id)."""
    fake_upload(monkeypatch)
    _, tokens = await register_and_login(client)
    headers = auth_headers(tokens)
    await client.post(
        "/api/v1/sellers",
        json={"business_name": unique_name("Business")},
        headers=headers,
    )
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
    approved = await client.post(
        f"/api/v1/sellers/{seller_id}/approve", headers=auth_headers(admin_tokens)
    )
    assert approved.status_code == 200
    return tokens, seller_id


async def publish_product_with_listing(
    client: AsyncClient,
    db: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
    *,
    price: float = 100.0,
    stock: int = 20,
) -> dict:
    admin_tokens = await make_admin(client, db)
    admin_headers = auth_headers(admin_tokens)

    category_resp = await client.post(
        "/api/v1/categories",
        json={"name": unique_name("Category")},
        headers=admin_headers,
    )
    category_id = category_resp.json()["data"]["id"]
    attribute_resp = await client.post(
        "/api/v1/attributes", json={"name": unique_name("Attr")}, headers=admin_headers
    )
    attribute_id = attribute_resp.json()["data"]["id"]

    seller_tokens, seller_id = await make_active_seller(client, db, monkeypatch)
    seller_headers = auth_headers(seller_tokens)

    product_resp = await client.post(
        "/api/v1/products",
        json={"category_id": category_id, "name": unique_name("Product")},
        headers=seller_headers,
    )
    product_id = product_resp.json()["data"]["id"]
    await client.post(
        f"/api/v1/products/{product_id}/images",
        data={"is_primary": "true"},
        files={"file": ("p.jpg", b"fake-bytes", "image/jpeg")},
        headers=seller_headers,
    )
    variant_resp = await client.post(
        f"/api/v1/products/{product_id}/variants",
        json={"attribute_values": [{"attribute_id": attribute_id, "value": "Black"}]},
        headers=seller_headers,
    )
    variant_id = variant_resp.json()["data"]["id"]
    await client.post(f"/api/v1/products/{product_id}/submit", headers=seller_headers)
    await client.post(f"/api/v1/products/{product_id}/approve", headers=admin_headers)

    listing_resp = await client.post(
        "/api/v1/listings",
        json={"variant_id": variant_id, "price": price, "stock": stock},
        headers=seller_headers,
    )
    listing_id = listing_resp.json()["data"]["id"]
    await client.post(f"/api/v1/listings/{listing_id}/submit", headers=seller_headers)
    await client.post(f"/api/v1/listings/{listing_id}/approve", headers=admin_headers)

    return {
        "seller_tokens": seller_tokens,
        "seller_id": seller_id,
        "listing_id": listing_id,
        "product_id": product_id,
        "variant_id": variant_id,
        "price": price,
        "stock": stock,
    }


async def make_buyer(client: AsyncClient) -> dict:
    _, tokens = await register_and_login(client)
    return auth_headers(tokens)


async def buy_single_line(
    client: AsyncClient,
    buyer_headers: dict,
    listing_id: uuid.UUID,
    quantity: int = 1,
    db: AsyncSession | None = None,
) -> dict:
    """Add one listing to the buyer's cart, check out, initiate an Airtel
    Money payment, have the buyer report it, then have an admin confirm the
    money arrived (this is what actually records revenue + opens seller
    orders). Returns the order_detail plus the *confirmed* payment response
    (which includes `revenue`)."""
    await client.post(
        "/api/v1/carts/items",
        json={"listing_id": str(listing_id), "quantity": quantity},
        headers=buyer_headers,
    )
    order_resp = await client.post(
        "/api/v1/orders",
        json={
            "shipping": {
                "recipient_name": "Mama",
                "phone": "+250700000000",
                "district": "Gasabo",
            }
        },
        headers=buyer_headers,
    )
    assert order_resp.status_code == 201
    order = order_resp.json()["data"]
    payment = await client.post(
        "/api/v1/payments",
        json={
            "order_id": order["id"],
            "momo_phone": "+250788000001",
            "airtel_phone": "+250722000002",
        },
        headers=buyer_headers,
    )
    payment_id = payment.json()["data"]["id"]
    reported = await client.post(
        f"/api/v1/payments/{payment_id}/paid",
        json={},
        headers=buyer_headers,
    )
    assert reported.status_code == 200
    assert reported.json()["data"]["status"] == "awaiting"
    assert db is not None, "buy_single_line requires db to confirm as admin"
    admin_tokens = await make_admin(client, db)
    confirmed = await client.post(
        f"/api/v1/payments/{payment_id}/confirm",
        json={},
        headers=auth_headers(admin_tokens),
    )
    assert confirmed.status_code == 200
    return {"order": order, "payment": confirmed.json()["data"]}


async def make_premium_plan(
    db: AsyncSession, *, commission_rate: float = 7
) -> uuid.UUID:
    plan = await PremiumPlanRepository(db).create(
        plan=PremiumPlan(
            code=f"cm-{uuid.uuid4().hex[:10]}",
            name="Commerce Premium",
            price=10,
            currency="USD",
            duration_days=30,
            commission_rate=commission_rate,
            is_active=True,
        )
    )
    await db.commit()
    return plan.id


# ── cart ─────────────────────────────────────────────────────────────────


async def test_cart_add_list_and_clear(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    buyer_headers = await make_buyer(client)
    ctx = await publish_product_with_listing(client, db, monkeypatch)

    added = await client.post(
        "/api/v1/carts/items",
        json={"listing_id": str(ctx["listing_id"]), "quantity": 2},
        headers=buyer_headers,
    )
    assert added.status_code == 201
    data = added.json()["data"]
    assert data["item_count"] == 1
    assert data["total"] == pytest.approx(200.0)
    assert data["items"][0]["quantity"] == 2

    cart = await client.get("/api/v1/carts", headers=buyer_headers)
    assert cart.json()["data"]["items"][0]["product_name"]

    cleared = await client.delete("/api/v1/carts", headers=buyer_headers)
    assert cleared.status_code == 200
    empty = await client.get("/api/v1/carts", headers=buyer_headers)
    assert empty.json()["data"]["item_count"] == 0


# ── checkout ─────────────────────────────────────────────────────────────


async def test_checkout_empty_cart_is_rejected(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    buyer_headers = await make_buyer(client)
    resp = await client.post(
        "/api/v1/orders",
        json={"shipping": {"recipient_name": "X", "phone": "1"}},
        headers=buyer_headers,
    )
    assert resp.status_code == 400


async def test_checkout_creates_order_and_snapshot(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    buyer_headers = await make_buyer(client)
    ctx = await publish_product_with_listing(client, db, monkeypatch, price=100.0)

    await client.post(
        "/api/v1/carts/items",
        json={"listing_id": str(ctx["listing_id"]), "quantity": 1},
        headers=buyer_headers,
    )
    order_resp = await client.post(
        "/api/v1/orders",
        json={
            "shipping": {
                "recipient_name": "Mama",
                "phone": "+250700000000",
                "district": "Gasabo",
            }
        },
        headers=buyer_headers,
    )
    assert order_resp.status_code == 201
    order = order_resp.json()["data"]
    assert order["total_amount"] == pytest.approx(100.0)
    assert order["subtotal"] == pytest.approx(100.0)
    assert order["payment_status"] == "pending"
    assert order["shipping"]["recipient_name"] == "Mama"
    assert len(order["items"]) == 1
    assert order["items"][0]["seller_id"] == ctx["seller_id"]
    assert order["items"][0]["unit_price"] == pytest.approx(100.0)

    # cart should be cleared after checkout
    cart = await client.get("/api/v1/carts", headers=buyer_headers)
    assert cart.json()["data"]["item_count"] == 0


async def test_checkout_rejects_insufficient_stock(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    buyer_headers = await make_buyer(client)
    ctx = await publish_product_with_listing(
        client, db, monkeypatch, price=100.0, stock=2
    )

    # adding more than available stock still loads, but checkout rejects it
    await client.post(
        "/api/v1/carts/items",
        json={"listing_id": str(ctx["listing_id"]), "quantity": 5},
        headers=buyer_headers,
    )
    resp = await client.post(
        "/api/v1/orders",
        json={"shipping": {"recipient_name": "M", "phone": "1"}},
        headers=buyer_headers,
    )
    assert resp.status_code == 400

    # clearing and buying within stock succeeds
    await client.delete("/api/v1/carts", headers=buyer_headers)
    await client.post(
        "/api/v1/carts/items",
        json={"listing_id": str(ctx["listing_id"]), "quantity": 2},
        headers=buyer_headers,
    )
    ok = await client.post(
        "/api/v1/orders",
        json={"shipping": {"recipient_name": "M", "phone": "1"}},
        headers=buyer_headers,
    )
    assert ok.status_code == 201
    assert ok.json()["data"]["total_amount"] == pytest.approx(200.0)


# ── payment + revenue: the money math ────────────────────────────────────


async def test_basic_seller_pays_12_percent(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    buyer_headers = await make_buyer(client)
    ctx = await publish_product_with_listing(client, db, monkeypatch, price=100.0)

    result = await buy_single_line(client, buyer_headers, ctx["listing_id"], db=db)
    order = result["order"]
    payment = result["payment"]

    # the checkout snapshot is pre-payment; re-fetch to see the paid state
    detail = await client.get(f"/api/v1/orders/{order['id']}", headers=buyer_headers)
    assert detail.status_code == 200
    refreshed = detail.json()["data"]
    assert refreshed["payment_status"] == "paid"
    assert refreshed["paid_at"] is not None
    assert payment["revenue"] == 1

    admin_tokens = await make_admin(client, db)
    lines = await client.get(
        f"/api/v1/revenue/order/{order['id']}", headers=auth_headers(admin_tokens)
    )
    assert lines.status_code == 200
    breakdown = lines.json()["data"]
    assert len(breakdown) == 1
    line = breakdown[0]
    assert line["seller_id"] == ctx["seller_id"]
    assert line["amount"] == pytest.approx(100.0)
    assert line["revenue_rate"] == pytest.approx(12.0)
    assert line["commission_amount"] == pytest.approx(12.0)
    assert line["seller_earning"] == pytest.approx(88.0)
    # escrow: right after payment the seller's earning is held (not yet released)
    assert line["status"] == "held"
    assert line["released_at"] is None


async def test_premium_seller_pays_7_percent(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    buyer_headers = await make_buyer(client)
    ctx = await publish_product_with_listing(client, db, monkeypatch, price=100.0)

    plan_id = await make_premium_plan(db, commission_rate=7)
    subscribed = await client.post(
        "/api/v1/premium/subscribe",
        json={"plan_id": str(plan_id)},
        headers=auth_headers(ctx["seller_tokens"]),
    )
    assert subscribed.status_code == 201

    result = await buy_single_line(client, buyer_headers, ctx["listing_id"], db=db)
    order = result["order"]

    admin_tokens = await make_admin(client, db)
    lines = await client.get(
        f"/api/v1/revenue/order/{order['id']}", headers=auth_headers(admin_tokens)
    )
    line = lines.json()["data"][0]
    assert line["revenue_rate"] == pytest.approx(7.0)
    assert line["commission_amount"] == pytest.approx(7.0)
    assert line["seller_earning"] == pytest.approx(93.0)


async def test_idempotent_reports_and_confirms_do_not_double_credit(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    buyer_headers = await make_buyer(client)
    ctx = await publish_product_with_listing(client, db, monkeypatch, price=100.0)
    admin_headers = auth_headers(await make_admin(client, db))

    await client.post(
        "/api/v1/carts/items",
        json={"listing_id": str(ctx["listing_id"]), "quantity": 1},
        headers=buyer_headers,
    )
    order_resp = await client.post(
        "/api/v1/orders",
        json={"shipping": {"recipient_name": "M", "phone": "2"}},
        headers=buyer_headers,
    )
    order_id = order_resp.json()["data"]["id"]
    payment = await client.post(
        "/api/v1/payments",
        json={
            "order_id": order_id,
            "momo_phone": "+250788000001",
            "airtel_phone": "+250722000002",
        },
        headers=buyer_headers,
    )
    payment_id = payment.json()["data"]["id"]

    # buyer reports once -> awaiting; a second report is rejected (idempotent)
    first = await client.post(
        f"/api/v1/payments/{payment_id}/paid", json={}, headers=buyer_headers
    )
    assert first.status_code == 200
    assert first.json()["data"]["status"] == "awaiting"
    second = await client.post(
        f"/api/v1/payments/{payment_id}/paid", json={}, headers=buyer_headers
    )
    assert second.status_code == 400

    # admin confirms once -> paid + revenue; a second confirm is rejected
    confirm1 = await client.post(
        f"/api/v1/payments/{payment_id}/confirm", json={}, headers=admin_headers
    )
    assert confirm1.status_code == 200
    assert confirm1.json()["data"]["revenue"] == 1
    assert confirm1.json()["data"]["status"] == "paid"
    confirm2 = await client.post(
        f"/api/v1/payments/{payment_id}/confirm", json={}, headers=admin_headers
    )
    assert confirm2.status_code == 400

    lines = await client.get(
        f"/api/v1/revenue/order/{order_id}", headers=admin_headers
    )
    assert len(lines.json()["data"]) == 1
    assert lines.json()["data"][0]["commission_amount"] == pytest.approx(12.0)


# ── addresses ────────────────────────────────────────────────────────────


async def test_create_and_use_saved_address(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    buyer_headers = await make_buyer(client)
    ctx = await publish_product_with_listing(client, db, monkeypatch, price=50.0)

    created = await client.post(
        "/api/v1/addresses",
        json={
            "recipient_name": "Papa",
            "phone": "+250788000000",
            "district": "Kicukiro",
            "is_default": True,
        },
        headers=buyer_headers,
    )
    assert created.status_code == 201
    address_id = created.json()["data"]["id"]

    await client.post(
        "/api/v1/carts/items",
        json={"listing_id": str(ctx["listing_id"]), "quantity": 1},
        headers=buyer_headers,
    )
    order_resp = await client.post(
        "/api/v1/orders",
        json={"shipping_address_id": str(address_id)},
        headers=buyer_headers,
    )
    assert order_resp.status_code == 201
    order = order_resp.json()["data"]
    assert order["shipping"]["recipient_name"] == "Papa"
    assert order["total_amount"] == pytest.approx(50.0)

    # editing the saved address must not change the frozen order snapshot
    await client.patch(
        f"/api/v1/addresses/{address_id}",
        json={"recipient_name": "Changed"},
        headers=buyer_headers,
    )
    after = await client.get(
        f"/api/v1/orders/{order['id']}", headers=buyer_headers
    )
    assert after.json()["data"]["shipping"]["recipient_name"] == "Papa"


# ── mobile money: the Momo request + callback ────────────────────────────


async def test_momo_payment_holds_phones_and_request_reference(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    buyer_headers = await make_buyer(client)
    ctx = await publish_product_with_listing(client, db, monkeypatch, price=100.0)

    await client.post(
        "/api/v1/carts/items",
        json={"listing_id": str(ctx["listing_id"]), "quantity": 1},
        headers=buyer_headers,
    )
    order_resp = await client.post(
        "/api/v1/orders",
        json={"shipping": {"recipient_name": "M", "phone": "3"}},
        headers=buyer_headers,
    )
    order = order_resp.json()["data"]

    created = await client.post(
        "/api/v1/payments",
        json={
            "order_id": order["id"],
            "momo_phone": "+250788111111",
            "airtel_phone": "+250722222222",
        },
        headers=buyer_headers,
    )
    assert created.status_code == 201
    pay = created.json()["data"]
    assert pay["status"] == "pending"
    assert pay["momo_phone"] == "+250788111111"
    assert pay["airtel_phone"] == "+250722222222"
    assert pay["method"] == "airtel_money"
    assert pay["provider_ref"].startswith("MOMO-")
    assert pay["currency"] == "RWF"

    confirm = await client.post(
        f"/api/v1/payments/{pay['id']}/paid", json={}, headers=buyer_headers
    )
    assert confirm.status_code == 200
    assert confirm.json()["data"]["status"] == "paid"
    assert confirm.json()["data"]["revenue"] == 1


# ── seller fulfillment: seller_orders + shipments ────────────────────────


async def test_seller_fulfillment_lifecycle(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    buyer_headers = await make_buyer(client)
    ctx = await publish_product_with_listing(client, db, monkeypatch, price=100.0)
    seller_headers = auth_headers(ctx["seller_tokens"])

    # buy + pay -> should open exactly one pending seller_order for the seller
    await buy_single_line(client, buyer_headers, ctx["listing_id"], db=db)

    mine = await client.get("/api/v1/orders/seller", headers=seller_headers)
    assert mine.status_code == 200
    rows = mine.json()["data"]
    assert len(rows) == 1
    seller_order = rows[0]
    assert seller_order["status"] == "pending"
    seller_order_id = seller_order["id"]

    # pending -> accepted
    accepted = await client.post(
        f"/api/v1/orders/seller/{seller_order_id}/accept", headers=seller_headers
    )
    assert accepted.status_code == 200
    assert accepted.json()["data"]["status"] == "accepted"

    # rejecting after accept is invalid
    rejected_late = await client.post(
        f"/api/v1/orders/seller/{seller_order_id}/reject",
        json={"reason": "late"},
        headers=seller_headers,
    )
    assert rejected_late.status_code == 400

    # accepted -> shipped (creates a shipment)
    shipped = await client.post(
        f"/api/v1/orders/seller/{seller_order_id}/ship",
        json={"carrier": "UPS", "tracking_number": "TRK-1", "notes": "fragile"},
        headers=seller_headers,
    )
    assert shipped.status_code == 200
    data = shipped.json()["data"]
    assert data["status"] == "shipped"
    assert data["shipment"]["carrier"] == "UPS"
    assert data["shipment"]["status"] == "shipped"
    shipment_id = data["shipment"]["id"]

    # shipping before accept is invalid
    overship = await client.post(
        f"/api/v1/orders/seller/{seller_order_id}/ship",
        json={},
        headers=seller_headers,
    )
    assert overship.status_code == 400

    # shipped -> delivered
    delivered = await client.post(
        f"/api/v1/orders/seller/shipments/{shipment_id}/deliver",
        headers=seller_headers,
    )
    assert delivered.status_code == 200
    assert delivered.json()["data"]["status"] == "delivered"
    assert delivered.json()["data"]["shipment"]["status"] == "delivered"


# ── closing the loop: buyer sees fulfillment + confirms receipt ──────────


async def test_buyer_sees_fulfillment_and_receives_order(
    client: AsyncClient, db: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    buyer_headers = await make_buyer(client)
    ctx = await publish_product_with_listing(client, db, monkeypatch, price=100.0)
    seller_headers = auth_headers(ctx["seller_tokens"])

    result = await buy_single_line(client, buyer_headers, ctx["listing_id"], db=db)
    order = result["order"]
    order_id = order["id"]

    # before any seller action, the buyer's detail shows a pending seller slice
    detail = await client.get(f"/api/v1/orders/{order_id}", headers=buyer_headers)
    fulfillment = detail.json()["data"]["fulfillment"]
    assert len(fulfillment) == 1
    assert fulfillment[0]["seller_id"] == ctx["seller_id"]
    assert fulfillment[0]["status"] == "pending"
    assert detail.json()["data"]["completed_at"] is None

    # seller ships -> buyer detail now shows shipped with a shipment
    seller_order_id = fulfillment[0]["id"]
    await client.post(
        f"/api/v1/orders/seller/{seller_order_id}/accept", headers=seller_headers
    )
    shipped = await client.post(
        f"/api/v1/orders/seller/{seller_order_id}/ship",
        json={"carrier": "Carrier", "tracking_number": "T1"},
        headers=seller_headers,
    )
    assert shipped.json()["data"]["status"] == "shipped"

    detail2 = await client.get(f"/api/v1/orders/{order_id}", headers=buyer_headers)
    ship_row = detail2.json()["data"]["fulfillment"][0]
    assert ship_row["status"] == "shipped"
    assert ship_row["shipment"]["tracking_number"] == "T1"

    # buyer confirms receipt -> order completed (final step of the loop)
    received = await client.post(
        f"/api/v1/orders/{order_id}/receive", headers=buyer_headers
    )
    assert received.status_code == 200
    assert received.json()["data"]["completed_at"] is not None

    # idempotent: receiving again stays completed
    again = await client.post(
        f"/api/v1/orders/{order_id}/receive", headers=buyer_headers
    )
    assert again.status_code == 200
    assert again.json()["data"]["completed_at"] == received.json()["data"]["completed_at"]

    # escrow: confirming receipt releases the seller's held earning exactly once
    admin_tokens = await make_admin(client, db)
    breakdown = (
        await client.get(
            f"/api/v1/revenue/order/{order_id}", headers=auth_headers(admin_tokens)
        )
    ).json()["data"]
    assert len(breakdown) == 1
    assert breakdown[0]["status"] == "released"
    assert breakdown[0]["released_at"] is not None

    # a non-buyer cannot receive / a random account 404s
    stranger_headers = await make_buyer(client)
    blocked = await client.post(
        f"/api/v1/orders/{order_id}/receive", headers=stranger_headers
    )
    assert blocked.status_code == 404
