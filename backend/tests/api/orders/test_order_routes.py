"""Orders through the HTTP API, against a real PostgreSQL database.

Two shops (Amina's and Brian's) and two buyers (Carol and Dave). Payment
confirmation, which the payments feature will do, is simulated by calling
`OrderService.mark_paid` the way that feature will.
"""

import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.modules.authorization.authorization_service import AuthorizationService
from app.modules.categories.category_service import CategoryService
from app.modules.orders.order_model import Order, OrderItem, SellerOrder, SellerOrderEvent
from app.modules.orders.order_service import OrderService, derive_order_status, split_commission
from app.modules.products.product_service import ProductService
from app.modules.seller_plans.seller_plan_service import SellerPlanService
from app.modules.sellers.seller_service import SellerService
from app.modules.wallets.wallet_service import WalletService

API = "/api/v1"
ORDERS = f"{API}/orders"
MY_ORDERS = f"{ORDERS}/mine"
SHOP_ORDERS = f"{API}/seller-orders/mine"
JPEG = b"\xff\xd8\xff\xe0" + b"jpeg-bytes" * 20
DELIVERY = {
    "recipient_name": "Carol Mukamana",
    "recipient_phone": "+250788999000",
    "province": "Kigali",
    "district": "Kicukiro",
    "sector": "Niboye",
    "address": "KK 15 Rd, blue gate",
}


class Shop:
    def __init__(self, actor, category_id: str) -> None:
        self.headers = actor.headers
        self.account_id = actor.id
        self.seller_id = actor.seller_id
        self.category_id = category_id


@pytest.fixture
def make_shop(db_client: AsyncClient, sign_up, open_shop):
    async def _make_shop(email: str, name: str) -> Shop:
        actor = await sign_up(email)
        actor.seller_id = await open_shop(actor, name)
        category = await db_client.post(
            f"{API}/categories", json={"name": "Things"}, headers=actor.headers
        )
        category_id = category.json()["data"]["id"]
        await db_client.post(
            f"{API}/categories/{category_id}/attributes",
            json={"name": "Storage", "data_type": "number", "unit": "GB"},
            headers=actor.headers,
        )
        return Shop(actor, category_id)

    return _make_shop


@pytest.fixture
async def amina(make_shop) -> Shop:
    return await make_shop("amina@example.com", "Amina Shop")


@pytest.fixture
async def brian(make_shop) -> Shop:
    return await make_shop("brian@example.com", "Brian Shop")


@pytest.fixture
async def carol(sign_up):
    return await sign_up("carol@example.com")


@pytest.fixture
async def dave(sign_up):
    return await sign_up("dave@example.com")


@pytest.fixture
def sell(db_client: AsyncClient):
    """Put a product on sale in a shop. Returns the product id."""

    async def _sell(shop: Shop, name: str, price: str, **attributes: object) -> str:
        created = await db_client.post(
            f"{API}/products",
            json={
                "name": name,
                "price": price,
                "category_id": shop.category_id,
                "attributes": attributes,
            },
            headers=shop.headers,
        )
        assert created.status_code == 201, created.text
        product_id = created.json()["data"]["id"]
        await db_client.post(
            f"{API}/products/mine/{product_id}/images",
            files={"file": ("photo.jpg", JPEG)},
            headers=shop.headers,
        )
        published = await db_client.post(
            f"{API}/products/mine/{product_id}/publish", headers=shop.headers
        )
        assert published.status_code == 200, published.text
        return product_id

    return _sell


@pytest.fixture
async def default_rate(db_client: AsyncClient, admin) -> None:
    """MUHUZE's commission for sellers without a plan: 10%."""
    response = await db_client.post(
        f"{API}/commission-rates/default", json={"rate": "10"}, headers=admin.headers
    )
    assert response.status_code == 201, response.text


@pytest.fixture
def place(db_client: AsyncClient):
    async def _place(buyer, *items: tuple[str, int], **fields: object) -> dict:
        payload = {
            "items": [{"product_id": product_id, "quantity": q} for product_id, q in items],
            "delivery": DELIVERY,
            **fields,
        }
        response = await db_client.post(ORDERS, json=payload, headers=buyer.headers)
        assert response.status_code == 201, response.text
        return response.json()["data"]

    return _place


@pytest.fixture
def pay(session_factory, file_storage):
    """What the payments feature does when a payment is confirmed."""

    async def _pay(order: dict) -> None:
        async with session_factory() as session:
            sellers = SellerService(session, AuthorizationService(session), file_storage)
            products = ProductService(session, CategoryService(session), sellers, file_storage)
            service = OrderService(
                session,
                products,
                SellerPlanService(session, sellers),
                sellers,
                WalletService(session),
            )
            await service.mark_paid(uuid.UUID(order["id"]))
            await session.commit()

    return _pay


def part(order: dict, shop_name: str) -> dict:
    return next(p for p in order["seller_orders"] if p["seller_name"] == shop_name)


async def shop_step(db_client: AsyncClient, shop: Shop, seller_order_id: str, step: str, **body):
    return await db_client.post(
        f"{SHOP_ORDERS}/{seller_order_id}/{step}", json=body or None, headers=shop.headers
    )


# ── Pure rules ───────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("subtotal", "rate", "commission", "seller_amount"),
    [
        ("100000.00", "5", "5000.00", "95000.00"),
        ("100000.00", "0", "0.00", "100000.00"),
        ("100000.00", "100", "100000.00", "0.00"),
        ("104999.99", "7.5", "7875.00", "97124.99"),  # 7874.99925 rounds up
        ("0.10", "5", "0.01", "0.09"),  # 0.005 rounds half up
        ("0.09", "5", "0.00", "0.09"),  # 0.0045 rounds down
        ("33333.33", "33.33", "11109.999", None),
    ],
)
def test_commission_split_always_adds_up(
    subtotal: str, rate: str, commission: str, seller_amount: str | None
) -> None:
    muhuze, seller = split_commission(Decimal(subtotal), Decimal(rate))

    assert muhuze + seller == Decimal(subtotal)  # nothing is lost or created by rounding
    assert muhuze == muhuze.quantize(Decimal("0.01"))
    if seller_amount is not None:
        assert (muhuze, seller) == (Decimal(commission), Decimal(seller_amount))


@pytest.mark.parametrize(
    ("paid", "cancelled", "parts", "expected"),
    [
        (False, False, ["awaiting_payment"], "awaiting_payment"),
        (False, True, ["cancelled", "cancelled"], "cancelled"),
        (True, False, ["pending", "pending"], "in_progress"),
        (True, False, ["completed", "shipped"], "in_progress"),
        (True, False, ["rejected", "accepted"], "in_progress"),
        (True, False, ["completed", "completed"], "completed"),
        (True, False, ["completed", "rejected"], "completed"),  # something was bought
        (True, False, ["rejected", "rejected"], "cancelled"),  # nothing was bought
    ],
)
def test_order_status_is_derived_from_payment_and_parts(
    paid: bool, cancelled: bool, parts: list[str], expected: str
) -> None:
    order = Order(paid_at=object() if paid else None, cancelled_at=object() if cancelled else None)
    assert derive_order_status(order, parts).value == expected


# ── Placing an order ─────────────────────────────────────────────────────


async def test_one_checkout_is_split_into_a_part_per_shop(
    db_client: AsyncClient, amina, brian, carol, sell, default_rate, place
) -> None:
    phone = await sell(amina, "Galaxy S24", "850000", storage=256)
    case = await sell(amina, "Phone case", "2500")
    laptop = await sell(brian, "Laptop", "450000")

    order = await place(carol, (phone, 1), (case, 2), (laptop, 1), note="Call before delivery")

    assert order["order_number"].startswith("MHZ-")
    assert order["status"] == "awaiting_payment"
    assert order["currency"] == "RWF"
    assert order["total_amount"] == "1305000.00"  # 850000 + 2 × 2500 + 450000
    assert order["paid_at"] is None
    assert order["delivery"] == {**DELIVERY, "note": "Call before delivery"}
    assert [p["seller_name"] for p in order["seller_orders"]] == ["Amina Shop", "Brian Shop"]

    amina_part = part(order, "Amina Shop")
    assert amina_part["seller_id"] == amina.seller_id
    assert amina_part["status"] == "awaiting_payment"
    assert amina_part["subtotal"] == "855000.00"
    assert [
        (i["product_name"], i["unit_price"], i["quantity"], i["line_total"])
        for i in amina_part["items"]
    ] == [("Galaxy S24", "850000.00", 1, "850000.00"), ("Phone case", "2500.00", 2, "5000.00")]
    galaxy = amina_part["items"][0]
    assert galaxy["product_id"] == phone
    assert galaxy["attributes"] == [{"name": "Storage", "value": 256, "unit": "GB"}]
    assert galaxy["image_url"].startswith("https://images.example.test/")
    assert part(order, "Brian Shop")["subtotal"] == "450000.00"
    # The buyer is never shown what MUHUZE or the seller earns.
    assert "commission_amount" not in amina_part
    assert "seller_amount" not in amina_part

    fetched = await db_client.get(f"{MY_ORDERS}/{order['id']}", headers=carol.headers)
    assert fetched.json()["data"] == order


async def test_prices_and_totals_sent_by_the_client_are_ignored(
    db_client: AsyncClient, amina, carol, sell, default_rate
) -> None:
    phone = await sell(amina, "Galaxy S24", "850000")

    response = await db_client.post(
        ORDERS,
        json={
            "items": [{"product_id": phone, "quantity": 2, "unit_price": "1", "price": "1"}],
            "delivery": DELIVERY,
            "total_amount": "1",
            "seller_id": str(uuid.uuid4()),
            "status": "completed",
        },
        headers=carol.headers,
    )

    assert response.status_code == 201
    order = response.json()["data"]
    assert order["total_amount"] == "1700000.00"
    assert order["status"] == "awaiting_payment"
    assert order["seller_orders"][0]["items"][0]["unit_price"] == "850000.00"


async def test_each_shops_commission_is_snapshotted_from_its_own_terms(
    db_client: AsyncClient, admin, amina, brian, carol, sell, default_rate, place, session_factory
) -> None:
    plan = (
        await db_client.post(
            f"{API}/seller-plans",
            json={
                "code": "business",
                "name": "Business",
                "price": "30000",
                "duration_days": 30,
                "commission_rate": "7.5",
            },
            headers=admin.headers,
        )
    ).json()["data"]
    subscription = (
        await db_client.post(
            f"{API}/seller-subscriptions",
            json={"seller_id": amina.seller_id, "plan_id": plan["id"]},
            headers=admin.headers,
        )
    ).json()["data"]
    order = await place(
        carol,
        (await sell(amina, "Galaxy S24", "104999.99"), 1),
        (await sell(brian, "Laptop", "450000"), 1),
    )

    staff_view = (await db_client.get(f"{ORDERS}/{order['id']}", headers=admin.headers)).json()
    split = {
        p["seller_name"]: (
            p["subtotal"],
            p["commission_rate"],
            p["commission_amount"],
            p["seller_amount"],
            p["terms_source"],
            p["plan_name"],
        )
        for p in staff_view["data"]["seller_orders"]
    }
    assert split == {
        # Amina is on a plan: 7.5%. Brian has none: the 10% default.
        "Amina Shop": ("104999.99", "7.50", "7875.00", "97124.99", "subscription", "Business"),
        "Brian Shop": ("450000.00", "10.00", "45000.00", "405000.00", "default", None),
    }
    # Persisted, with the exact source of each rate.
    async with session_factory() as session:
        rows = {
            row.seller_name: row
            for row in await session.scalars(
                select(SellerOrder).where(SellerOrder.order_id == uuid.UUID(order["id"]))
            )
        }
    assert str(rows["Amina Shop"].subscription_id) == subscription["id"]
    assert rows["Amina Shop"].default_rate_id is None
    assert rows["Brian Shop"].subscription_id is None
    assert rows["Brian Shop"].default_rate_id is not None


async def test_an_order_never_changes_when_the_product_or_the_rate_does(
    db_client: AsyncClient, admin, amina, carol, sell, default_rate, place
) -> None:
    phone = await sell(amina, "Galaxy S24", "100000", storage=128)
    order = await place(carol, (phone, 1))

    # Afterwards: a new name, price and details, and a new commission rate.
    await db_client.patch(
        f"{API}/products/mine/{phone}",
        json={"name": "Galaxy S25", "price": "120000", "attributes": {"storage": 512}},
        headers=amina.headers,
    )
    await db_client.post(
        f"{API}/commission-rates/default", json={"rate": "25"}, headers=admin.headers
    )

    buyer_view = (await db_client.get(f"{MY_ORDERS}/{order['id']}", headers=carol.headers)).json()
    item = buyer_view["data"]["seller_orders"][0]["items"][0]
    assert (item["product_name"], item["unit_price"]) == ("Galaxy S24", "100000.00")
    assert item["attributes"] == [{"name": "Storage", "value": 128, "unit": "GB"}]
    assert buyer_view["data"]["total_amount"] == "100000.00"
    staff_view = (await db_client.get(f"{ORDERS}/{order['id']}", headers=admin.headers)).json()
    seller_part = staff_view["data"]["seller_orders"][0]
    assert (seller_part["commission_rate"], seller_part["commission_amount"]) == (
        "10.00",
        "10000.00",
    )
    # A new order uses the new price and the new rate.
    new_order = await place(carol, (phone, 1))
    assert new_order["total_amount"] == "120000.00"


async def test_products_that_are_not_on_sale_cannot_be_ordered(
    db_client: AsyncClient, admin, amina, brian, carol, sell, default_rate
) -> None:
    on_sale = await sell(amina, "On sale", "1000")
    archived = await sell(amina, "Archived", "1000")
    await db_client.post(f"{API}/products/mine/{archived}/archive", headers=amina.headers)
    draft = (
        await db_client.post(
            f"{API}/products",
            json={"name": "Draft", "price": "1000", "category_id": amina.category_id},
            headers=amina.headers,
        )
    ).json()["data"]["id"]
    suspended_shop = await sell(brian, "From a suspended shop", "1000")
    await db_client.post(
        f"{API}/sellers/{brian.seller_id}/suspend",
        json={"reason": "Under investigation"},
        headers=admin.headers,
    )
    missing = str(uuid.uuid4())

    response = await db_client.post(
        ORDERS,
        json={
            "items": [
                {"product_id": p, "quantity": 1}
                for p in (on_sale, archived, draft, suspended_shop, missing)
            ],
            "delivery": DELIVERY,
        },
        headers=carol.headers,
    )

    assert response.status_code == 422
    message = response.json()["message"]
    assert message.startswith("These products are no longer available: ")
    for product_id in (archived, draft, suspended_shop, missing):
        assert product_id in message  # every problem product is named
    assert on_sale not in message
    # All or nothing: the one good product did not become an order.
    listed = await db_client.get(MY_ORDERS, headers=carol.headers)
    assert listed.json()["data"]["total"] == 0


async def test_a_seller_cannot_order_from_their_own_shop(
    db_client: AsyncClient, amina, brian, sell, default_rate, place
) -> None:
    own = await sell(amina, "Mine", "1000")
    theirs = await sell(brian, "Theirs", "1000")

    refused = await db_client.post(
        ORDERS,
        json={
            "items": [{"product_id": own, "quantity": 1}, {"product_id": theirs, "quantity": 1}],
            "delivery": DELIVERY,
        },
        headers=amina.headers,
    )

    assert refused.status_code == 422
    assert refused.json()["message"] == "You cannot order products from your own shop"
    # A seller is also a buyer: another shop's products are fine.
    assert (await place(amina, (theirs, 1)))["total_amount"] == "1000.00"


async def test_orders_need_a_commission_rate_to_exist(
    db_client: AsyncClient, amina, carol, sell
) -> None:
    phone = await sell(amina, "Galaxy S24", "1000")  # no default rate, and no plan

    response = await db_client.post(
        ORDERS,
        json={"items": [{"product_id": phone, "quantity": 1}], "delivery": DELIVERY},
        headers=carol.headers,
    )

    assert response.status_code == 422
    assert response.json()["message"] == "MUHUZE has not set its commission rate yet"


@pytest.mark.parametrize(
    "change",
    [
        {"items": []},
        {"items": [{"product_id": "not-a-uuid", "quantity": 1}]},
        {"items": [{"product_id": "00000000-0000-0000-0000-000000000001", "quantity": 0}]},
        {"items": [{"product_id": "00000000-0000-0000-0000-000000000001", "quantity": 1000}]},
        {"items": [{"product_id": "00000000-0000-0000-0000-000000000001", "quantity": 1}] * 2},
        {"items": [{"product_id": str(uuid.UUID(int=n)), "quantity": 1} for n in range(51)]},
        {"delivery": {**DELIVERY, "recipient_phone": "0788123456"}},
        {"delivery": {**DELIVERY, "district": ""}},
        {"delivery": None},
    ],
)
async def test_place_order_validates_its_input(db_client: AsyncClient, carol, change: dict) -> None:
    payload = {
        "items": [{"product_id": "00000000-0000-0000-0000-000000000001", "quantity": 1}],
        "delivery": DELIVERY,
        **change,
    }
    response = await db_client.post(ORDERS, json=payload, headers=carol.headers)
    assert response.status_code == 422


async def test_placing_an_order_needs_a_login(db_client: AsyncClient) -> None:
    response = await db_client.post(ORDERS, json={"items": [], "delivery": DELIVERY})
    assert response.status_code == 401


async def test_what_is_stored_adds_up(
    amina, brian, carol, sell, default_rate, place, session_factory
) -> None:
    order = await place(
        carol,
        (await sell(amina, "A", "33333.33"), 3),
        (await sell(amina, "B", "0.07"), 7),
        (await sell(brian, "C", "19999.99"), 2),
    )

    async with session_factory() as session:
        stored = await session.get(Order, uuid.UUID(order["id"]))
        parts = list(
            await session.scalars(select(SellerOrder).where(SellerOrder.order_id == stored.id))
        )
        items = list(
            await session.scalars(
                select(OrderItem).where(OrderItem.seller_order_id.in_([p.id for p in parts]))
            )
        )
        events = list(await session.scalars(select(SellerOrderEvent)))
    # Reproducible from the snapshots, bottom up (README §14, invariant 18).
    for item in items:
        assert item.line_total == item.unit_price * item.quantity
    for seller_part in parts:
        mine = [item for item in items if item.seller_order_id == seller_part.id]
        assert seller_part.subtotal == sum(item.line_total for item in mine)
        assert seller_part.commission_amount + seller_part.seller_amount == seller_part.subtotal
    assert stored.total_amount == sum(seller_part.subtotal for seller_part in parts)
    assert stored.total_amount == Decimal("140000.46")
    assert len(events) == 2  # one "created" event per shop
    assert {event.actor_account_id for event in events} == {uuid.UUID(carol.id)}


# ── Before payment ───────────────────────────────────────────────────────


async def test_sellers_do_not_see_an_order_until_it_is_paid(
    db_client: AsyncClient, amina, carol, sell, default_rate, place, pay
) -> None:
    order = await place(carol, (await sell(amina, "Galaxy S24", "1000"), 1))
    seller_order_id = order["seller_orders"][0]["id"]
    url = f"{SHOP_ORDERS}/{seller_order_id}"

    listed = await db_client.get(SHOP_ORDERS, headers=amina.headers)
    opened = await db_client.get(url, headers=amina.headers)
    accepted = await shop_step(db_client, amina, seller_order_id, "accept")

    assert listed.json()["data"]["total"] == 0
    assert opened.status_code == accepted.status_code == 404

    await pay(order)

    listed = await db_client.get(SHOP_ORDERS, headers=amina.headers)
    assert [o["id"] for o in listed.json()["data"]["items"]] == [seller_order_id]
    assert (await db_client.get(url, headers=amina.headers)).status_code == 200


async def test_the_buyer_can_cancel_only_while_unpaid(
    db_client: AsyncClient, amina, carol, sell, default_rate, place, pay
) -> None:
    phone = await sell(amina, "Galaxy S24", "1000")
    unpaid = await place(carol, (phone, 1))
    paid = await place(carol, (phone, 1))
    await pay(paid)

    cancelled = await db_client.post(
        f"{MY_ORDERS}/{unpaid['id']}/cancel",
        json={"reason": "Changed my mind"},
        headers=carol.headers,
    )
    twice = await db_client.post(
        f"{MY_ORDERS}/{unpaid['id']}/cancel", json={}, headers=carol.headers
    )
    too_late = await db_client.post(
        f"{MY_ORDERS}/{paid['id']}/cancel", json={}, headers=carol.headers
    )

    data = cancelled.json()["data"]
    assert (data["status"], data["cancel_reason"]) == ("cancelled", "Changed my mind")
    assert data["cancelled_at"] is not None
    assert [p["status"] for p in data["seller_orders"]] == ["cancelled"]
    assert twice.status_code == too_late.status_code == 409
    assert too_late.json()["message"] == "A paid order cannot be cancelled"
    # The seller never hears of an order that was cancelled before payment.
    listed = await db_client.get(SHOP_ORDERS, headers=amina.headers)
    assert [o["order_number"] for o in listed.json()["data"]["items"]] == [paid["order_number"]]


async def test_a_cancelled_order_cannot_be_paid_and_paying_twice_changes_nothing(
    db_client: AsyncClient, amina, carol, sell, default_rate, place, pay
) -> None:
    phone = await sell(amina, "Galaxy S24", "1000")
    cancelled = await place(carol, (phone, 1))
    await db_client.post(f"{MY_ORDERS}/{cancelled['id']}/cancel", json={}, headers=carol.headers)
    order = await place(carol, (phone, 1))

    with pytest.raises(Exception, match="cancelled order cannot be paid"):
        await pay(cancelled)
    await pay(order)
    first = (await db_client.get(f"{MY_ORDERS}/{order['id']}", headers=carol.headers)).json()
    await pay(order)  # the payment provider tells us again
    second = (await db_client.get(f"{MY_ORDERS}/{order['id']}", headers=carol.headers)).json()

    assert first["data"]["paid_at"] == second["data"]["paid_at"]
    history = await db_client.get(
        f"{SHOP_ORDERS}/{order['seller_orders'][0]['id']}", headers=amina.headers
    )
    assert [e["to_status"] for e in history.json()["data"]["events"]] == [
        "awaiting_payment",
        "pending",
    ]


# ── After payment: each shop handles its part ────────────────────────────


async def test_a_seller_takes_their_part_from_pending_to_delivered(
    db_client: AsyncClient, amina, carol, sell, default_rate, place, pay
) -> None:
    order = await place(carol, (await sell(amina, "Galaxy S24", "100000", storage=256), 2))
    await pay(order)
    seller_order_id = order["seller_orders"][0]["id"]

    opened = (await db_client.get(f"{SHOP_ORDERS}/{seller_order_id}", headers=amina.headers)).json()
    mine = opened["data"]
    assert mine["status"] == "pending"
    assert mine["order_number"] == order["order_number"]
    assert (mine["subtotal"], mine["commission_rate"], mine["commission_amount"]) == (
        "200000.00",
        "10.00",
        "20000.00",
    )
    assert mine["seller_amount"] == "180000.00"
    assert mine["delivery"]["recipient_phone"] == "+250788999000"  # where to deliver
    assert [(i["product_name"], i["quantity"]) for i in mine["items"]] == [("Galaxy S24", 2)]

    statuses = []
    for step in ("accept", "ship", "deliver"):
        response = await shop_step(db_client, amina, seller_order_id, step)
        assert response.status_code == 200, response.text
        statuses.append(response.json()["data"]["status"])
    assert statuses == ["accepted", "shipped", "delivered"]

    events = response.json()["data"]["events"]
    assert [(e["from_status"], e["to_status"]) for e in events] == [
        (None, "awaiting_payment"),
        ("awaiting_payment", "pending"),
        ("pending", "accepted"),
        ("accepted", "shipped"),
        ("shipped", "delivered"),
    ]
    # Who did each step is recorded: the buyer, the system, then the seller.
    assert [e["actor_account_id"] for e in events] == [
        carol.id,
        None,
        amina.account_id,
        amina.account_id,
        amina.account_id,
    ]


@pytest.mark.parametrize(
    ("done", "attempt"),
    [
        ([], "ship"),
        ([], "deliver"),
        (["accept"], "accept"),
        (["accept"], "deliver"),
        (["accept", "ship"], "accept"),
        (["accept", "ship", "deliver"], "ship"),
    ],
)
async def test_steps_cannot_be_skipped_or_repeated(
    db_client: AsyncClient, amina, carol, sell, default_rate, place, pay, done, attempt
) -> None:
    order = await place(carol, (await sell(amina, "Galaxy S24", "1000"), 1))
    await pay(order)
    seller_order_id = order["seller_orders"][0]["id"]
    for step in done:
        await shop_step(db_client, amina, seller_order_id, step)

    response = await shop_step(db_client, amina, seller_order_id, attempt)

    assert response.status_code == 409


async def test_a_seller_can_reject_only_while_pending_and_must_say_why(
    db_client: AsyncClient, amina, carol, sell, default_rate, place, pay
) -> None:
    phone = await sell(amina, "Galaxy S24", "1000")
    first, second = await place(carol, (phone, 1)), await place(carol, (phone, 1))
    await pay(first)
    await pay(second)
    first_id, second_id = first["seller_orders"][0]["id"], second["seller_orders"][0]["id"]

    no_reason = await shop_step(db_client, amina, first_id, "reject")
    rejected = await shop_step(
        db_client, amina, first_id, "reject", reason="Sold the last one yesterday"
    )
    await shop_step(db_client, amina, second_id, "accept")
    too_late = await shop_step(db_client, amina, second_id, "reject", reason="Changed my mind")

    assert no_reason.status_code == 422
    assert rejected.json()["data"]["status"] == "rejected"
    assert too_late.status_code == 409
    # The buyer sees why, and the order ends as cancelled: nothing was bought.
    buyer_view = (await db_client.get(f"{MY_ORDERS}/{first['id']}", headers=carol.headers)).json()
    assert buyer_view["data"]["status"] == "cancelled"
    assert buyer_view["data"]["seller_orders"][0]["status_reason"] == "Sold the last one yesterday"


async def test_shops_move_independently_and_the_order_follows(
    db_client: AsyncClient, amina, brian, carol, sell, default_rate, place, pay
) -> None:
    order = await place(
        carol, (await sell(amina, "Phone", "1000"), 1), (await sell(brian, "Laptop", "2000"), 1)
    )
    amina_id, brian_id = part(order, "Amina Shop")["id"], part(order, "Brian Shop")["id"]
    url = f"{MY_ORDERS}/{order['id']}"

    async def view() -> tuple[str, dict[str, str]]:
        data = (await db_client.get(url, headers=carol.headers)).json()["data"]
        return data["status"], {p["seller_name"]: p["status"] for p in data["seller_orders"]}

    assert (await view())[0] == "awaiting_payment"
    await pay(order)
    assert await view() == ("in_progress", {"Amina Shop": "pending", "Brian Shop": "pending"})

    await shop_step(db_client, amina, amina_id, "accept")
    await shop_step(db_client, amina, amina_id, "ship")
    await shop_step(db_client, brian, brian_id, "reject", reason="Out of stock, sorry")
    assert await view() == ("in_progress", {"Amina Shop": "shipped", "Brian Shop": "rejected"})

    received = await db_client.post(
        f"{url}/seller-orders/{amina_id}/confirm-receipt", headers=carol.headers
    )
    assert received.status_code == 200
    # One shop delivered, the other declined: the purchase is complete.
    assert await view() == ("completed", {"Amina Shop": "completed", "Brian Shop": "rejected"})


async def test_the_buyer_confirms_receipt_once_it_has_shipped(
    db_client: AsyncClient, amina, carol, dave, sell, default_rate, place, pay
) -> None:
    order = await place(carol, (await sell(amina, "Galaxy S24", "1000"), 1))
    await pay(order)
    seller_order_id = order["seller_orders"][0]["id"]
    url = f"{MY_ORDERS}/{order['id']}/seller-orders/{seller_order_id}/confirm-receipt"

    too_early = await db_client.post(url, headers=carol.headers)
    await shop_step(db_client, amina, seller_order_id, "accept")
    await shop_step(db_client, amina, seller_order_id, "ship")
    by_someone_else = await db_client.post(url, headers=dave.headers)
    wrong_part = await db_client.post(
        f"{MY_ORDERS}/{order['id']}/seller-orders/{uuid.uuid4()}/confirm-receipt",
        headers=carol.headers,
    )
    confirmed = await db_client.post(url, headers=carol.headers)
    twice = await db_client.post(url, headers=carol.headers)

    assert too_early.status_code == 409
    assert too_early.json()["message"] == "You can confirm receipt once the seller has shipped it"
    assert by_someone_else.status_code == wrong_part.status_code == 404
    assert confirmed.json()["data"]["status"] == "completed"
    assert twice.status_code == 409
    # A completed part is final for the seller too.
    assert (await shop_step(db_client, amina, seller_order_id, "deliver")).status_code == 409


# ── Who can see what ─────────────────────────────────────────────────────


async def test_buyers_see_only_their_own_orders(
    db_client: AsyncClient, amina, carol, dave, sell, default_rate, place
) -> None:
    phone = await sell(amina, "Galaxy S24", "1000")
    carols = await place(carol, (phone, 1))
    await place(dave, (phone, 2))

    listed = await db_client.get(MY_ORDERS, headers=carol.headers)
    theirs = await db_client.get(f"{MY_ORDERS}/{carols['id']}", headers=dave.headers)
    cancel = await db_client.post(
        f"{MY_ORDERS}/{carols['id']}/cancel", json={}, headers=dave.headers
    )

    assert [o["id"] for o in listed.json()["data"]["items"]] == [carols["id"]]
    assert theirs.status_code == cancel.status_code == 404
    assert theirs.json()["message"] == "Order not found"


async def test_a_seller_sees_only_their_own_shops_part(
    db_client: AsyncClient, amina, brian, carol, sell, default_rate, place, pay
) -> None:
    order = await place(
        carol, (await sell(amina, "Phone", "1000"), 1), (await sell(brian, "Laptop", "2000"), 1)
    )
    await pay(order)
    amina_id, brian_id = part(order, "Amina Shop")["id"], part(order, "Brian Shop")["id"]

    listed = await db_client.get(SHOP_ORDERS, headers=amina.headers)
    mine = await db_client.get(f"{SHOP_ORDERS}/{amina_id}", headers=amina.headers)
    theirs = await db_client.get(f"{SHOP_ORDERS}/{brian_id}", headers=amina.headers)
    act_on_theirs = await shop_step(db_client, amina, brian_id, "accept")
    as_buyer_page = await db_client.get(f"{MY_ORDERS}/{order['id']}", headers=amina.headers)

    assert [(o["id"], o["subtotal"]) for o in listed.json()["data"]["items"]] == [
        (amina_id, "1000.00")
    ]
    # Their own items and money only: not the other shop's, not the order total.
    data = mine.json()["data"]
    assert [i["product_name"] for i in data["items"]] == ["Phone"]
    assert "total_amount" not in data
    assert "2000.00" not in mine.text
    assert theirs.status_code == act_on_theirs.status_code == as_buyer_page.status_code == 404


async def test_a_sellers_order_list_can_be_filtered_by_status(
    db_client: AsyncClient, amina, carol, sell, default_rate, place, pay
) -> None:
    phone = await sell(amina, "Galaxy S24", "1000")
    waiting, in_hand = await place(carol, (phone, 1)), await place(carol, (phone, 1))
    await pay(waiting)
    await pay(in_hand)
    await shop_step(db_client, amina, in_hand["seller_orders"][0]["id"], "accept")

    async def numbers(**params: object) -> list[str]:
        response = await db_client.get(SHOP_ORDERS, params=params, headers=amina.headers)
        return sorted(o["order_number"] for o in response.json()["data"]["items"])

    assert await numbers() == sorted([waiting["order_number"], in_hand["order_number"]])
    assert await numbers(status="pending") == [waiting["order_number"]]
    assert await numbers(status="accepted") == [in_hand["order_number"]]
    assert await numbers(status="shipped") == []


async def test_only_an_active_seller_can_handle_shop_orders(
    db_client: AsyncClient, admin, amina, carol, sell, default_rate, place, pay
) -> None:
    order = await place(carol, (await sell(amina, "Galaxy S24", "1000"), 1))
    await pay(order)
    seller_order_id = order["seller_orders"][0]["id"]

    assert (await db_client.get(SHOP_ORDERS)).status_code == 401
    assert (await db_client.get(SHOP_ORDERS, headers=carol.headers)).status_code == 403

    await db_client.post(
        f"{API}/sellers/{amina.seller_id}/suspend",
        json={"reason": "Under investigation"},
        headers=admin.headers,
    )
    suspended = await shop_step(db_client, amina, seller_order_id, "accept")
    assert suspended.status_code == 403


async def test_staff_can_see_every_order_and_others_cannot(
    db_client: AsyncClient, admin, amina, carol, dave, sell, default_rate, place, pay
) -> None:
    phone = await sell(amina, "Galaxy S24", "1000")
    first, second = await place(carol, (phone, 1)), await place(dave, (phone, 1))
    await pay(second)

    everything = await db_client.get(ORDERS, headers=admin.headers)
    paid_only = await db_client.get(ORDERS, params={"status": "in_progress"}, headers=admin.headers)
    by_buyer = await db_client.get(
        ORDERS, params={"buyer_account_id": carol.id}, headers=admin.headers
    )
    by_number = await db_client.get(
        ORDERS, params={"q": first["order_number"].lower()}, headers=admin.headers
    )
    detail = await db_client.get(f"{ORDERS}/{first['id']}", headers=admin.headers)

    assert everything.json()["data"]["total"] == 2
    assert [o["id"] for o in paid_only.json()["data"]["items"]] == [second["id"]]
    assert [o["id"] for o in by_buyer.json()["data"]["items"]] == [first["id"]]
    assert [o["id"] for o in by_number.json()["data"]["items"]] == [first["id"]]
    assert detail.json()["data"]["buyer_account_id"] == carol.id
    for actor in (carol, amina):
        assert (await db_client.get(ORDERS, headers=actor.headers)).status_code == 403
        assert (
            await db_client.get(f"{ORDERS}/{first['id']}", headers=actor.headers)
        ).status_code == 403
    assert (await db_client.get(ORDERS)).status_code == 401
    assert (
        await db_client.get(f"{ORDERS}/{uuid.uuid4()}", headers=admin.headers)
    ).status_code == 404
