"""Services and service requests through the HTTP API, against a real
PostgreSQL database (README §7.5).

Pat is a cleaning provider, Amina sells goods, Carol buys. A service goes
request → accept → pay → done → confirmed, and from acceptance on it is an
ordinary order: the same commission, wallet, and settlement. The tests
assert what is PERSISTED wherever money or state is involved.
"""

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest
from httpx import AsyncClient
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.modules.orders.order_model import Order, SellerOrder
from app.modules.service_requests import service_request_service
from app.modules.service_requests.service_request_model import ServiceRequest

API = "/api/v1"
REQUESTS = f"{API}/service-requests"
MY_REQUESTS = f"{REQUESTS}/mine"
INCOMING = f"{REQUESTS}/incoming"
SHOP_ORDERS = f"{API}/seller-orders/mine"
JPEG = b"\xff\xd8\xff\xe0" + b"jpeg-bytes" * 20
BUSINESS_PHONE = "+250788123456"  # what `open_shop` applies with
KIGALI = ZoneInfo("Africa/Kigali")
CONTACT = {"name": "Carol Mukamana", "phone": "+250788999000"}
PLACE = {
    "province": "Kigali",
    "district": "Kicukiro",
    "sector": "Niboye",
    "address": "KK 15 Ave, house 12",
}
# Goods are delivered to the same place, without the street.
DELIVERY = {
    "recipient_name": CONTACT["name"],
    "recipient_phone": CONTACT["phone"],
    **{k: v for k, v in PLACE.items() if k != "address"},
}
EVERY_DAY = [{"weekday": d, "opens_at": "08:00", "closes_at": "18:00"} for d in range(1, 8)]
# Pat cleans homes in two districts, any day from 8 to 18, with no notice.
CLEANING = {
    "location": "at_customer",
    "duration_minutes": 180,
    "min_notice_hours": 0,
    "areas": ["Kicukiro", "Gasabo"],
    "hours": EVERY_DAY,
}


def soon(days: int = 3, hour: int = 10) -> str:
    """`days` from now at `hour` o'clock in Kigali: inside working hours."""
    day = datetime.now(KIGALI) + timedelta(days=days)
    return day.replace(hour=hour, minute=0, second=0, microsecond=0).isoformat()


@pytest.fixture
def listing(db_client: AsyncClient):
    """Put a published listing of the given kind in a seller's shop."""

    async def _listing(
        seller, name: str, price: str, kind: str, service: dict | None = None
    ) -> str:
        category = await db_client.post(
            f"{API}/categories", json={"name": f"{name} things"}, headers=seller.headers
        )
        assert category.status_code == 201, category.text
        created = await db_client.post(
            f"{API}/products",
            json={
                "kind": kind,
                "name": name,
                "price": price,
                "category_id": category.json()["data"]["id"],
                **({"service": service or CLEANING} if kind == "service" else {}),
            },
            headers=seller.headers,
        )
        assert created.status_code == 201, created.text
        product_id = created.json()["data"]["id"]
        await db_client.post(
            f"{API}/products/mine/{product_id}/images",
            files={"file": ("photo.jpg", JPEG)},
            headers=seller.headers,
        )
        published = await db_client.post(
            f"{API}/products/mine/{product_id}/publish", headers=seller.headers
        )
        assert published.status_code == 200, published.text
        return product_id

    return _listing


@pytest.fixture
async def market(db_client: AsyncClient, admin, sign_up, open_shop, listing):
    """A 10% default commission, an account to be paid on, Pat's cleaning
    service at 20,000, and Amina's kettle at 15,000."""
    rate = await db_client.post(
        f"{API}/commission-rates/default", json={"rate": "10"}, headers=admin.headers
    )
    assert rate.status_code == 201, rate.text
    destination = await db_client.post(
        f"{API}/payment-destinations",
        json={
            "method": "mobile_money",
            "provider": "Example Mobile Money",
            "account_reference": "0780000001",
            "registered_name": "MUHUZE EXAMPLE LTD",
        },
        headers=admin.headers,
    )
    assert destination.status_code == 201, destination.text

    class Market:
        destination_id = destination.json()["data"]["id"]

    Market.pat = await sign_up("pat@example.com")
    Market.pat.seller_id = await open_shop(Market.pat, "Pat Cleaning")
    Market.cleaning = await listing(Market.pat, "Home cleaning", "20000", "service")
    Market.amina = await sign_up("amina@example.com")
    Market.amina.seller_id = await open_shop(Market.amina, "Amina Shop")
    Market.kettle = await listing(Market.amina, "Kettle", "15000", "product")
    return Market


@pytest.fixture
async def carol(sign_up):
    return await sign_up("carol@example.com")


@pytest.fixture
def ask(db_client: AsyncClient, carol, market):
    """Carol requests a service. Returns the raw response."""

    async def _ask(service_id: str | None = None, **fields: object):
        payload = {
            "service_id": service_id or market.cleaning,
            "scheduled_for": soon(),
            "contact": CONTACT,
            "place": PLACE,
            "note": "Two bedrooms",
            **fields,
        }
        return await db_client.post(REQUESTS, json=payload, headers=carol.headers)

    return _ask


@pytest.fixture
def requested(ask):
    async def _requested(**fields: object) -> dict:
        response = await ask(**fields)
        assert response.status_code == 201, response.text
        return response.json()["data"]

    return _requested


@pytest.fixture
def accepted(db_client: AsyncClient, market, requested):
    """A request Pat has accepted. Returns the request, with its order."""

    async def _accepted() -> dict:
        request = await requested()
        response = await db_client.post(
            f"{INCOMING}/{request['id']}/accept", headers=market.pat.headers
        )
        assert response.status_code == 200, response.text
        return response.json()["data"]

    return _accepted


@pytest.fixture
def pay(db_client: AsyncClient, admin, carol, market):
    """Carol submits a payment for the order and staff approve it."""

    async def _pay(order_id: str) -> None:
        submitted = await db_client.post(
            f"{API}/orders/mine/{order_id}/payment",
            json={
                "destination_id": market.destination_id,
                "reference": f"MP-{uuid.uuid4().hex[:8]}",
                "payer_name": "Carol",
            },
            headers=carol.headers,
        )
        assert submitted.status_code == 201, submitted.text
        approved = await db_client.post(
            f"{API}/payments/{submitted.json()['data']['id']}/approve", headers=admin.headers
        )
        assert approved.status_code == 200, approved.text

    return _pay


@pytest.fixture
def paid(db_client: AsyncClient, market, accepted, pay):
    """An accepted, paid service. Returns (request, Pat's seller order id)."""

    async def _paid() -> tuple[dict, str]:
        request = await accepted()
        await pay(request["order"]["id"])
        shop_orders = await db_client.get(SHOP_ORDERS, headers=market.pat.headers)
        return request, shop_orders.json()["data"]["items"][0]["id"]

    return _paid


async def wallet(db_client: AsyncClient, seller) -> tuple[str, str]:
    """(pending, available)"""
    data = (await db_client.get(f"{API}/wallet/mine", headers=seller.headers)).json()["data"]
    return data["pending_balance"], data["available_balance"]


async def seller_order_of(session_factory, order_id: str) -> SellerOrder:
    async with session_factory() as session:
        return await session.scalar(
            select(SellerOrder).where(SellerOrder.order_id == uuid.UUID(order_id))
        )


# ── Listings ─────────────────────────────────────────────────────────────


async def test_the_storefront_lists_goods_by_default_and_services_on_request(
    db_client: AsyncClient, market
) -> None:
    goods = (await db_client.get(f"{API}/products")).json()["data"]["items"]
    services = (await db_client.get(f"{API}/products", params={"kind": "service"})).json()["data"]

    assert [(p["name"], p["kind"]) for p in goods] == [("Kettle", "product")]
    assert [(p["name"], p["kind"]) for p in services["items"]] == [("Home cleaning", "service")]
    own = await db_client.get(
        f"{API}/products/mine", params={"kind": "service"}, headers=market.pat.headers
    )
    assert own.json()["data"]["total"] == 1


async def test_a_listing_keeps_the_kind_it_was_created_with(db_client: AsyncClient, market) -> None:
    changed = await db_client.patch(
        f"{API}/products/mine/{market.cleaning}",
        json={"kind": "product", "name": "Deep cleaning"},
        headers=market.pat.headers,
    )

    assert changed.status_code == 200, changed.text
    assert (changed.json()["data"]["name"], changed.json()["data"]["kind"]) == (
        "Deep cleaning",
        "service",
    )


async def test_a_service_cannot_be_checked_out(
    db_client: AsyncClient, carol, market, session_factory
) -> None:
    response = await db_client.post(
        f"{API}/orders",
        json={
            "items": [
                {"product_id": market.kettle, "quantity": 1},
                {"product_id": market.cleaning, "quantity": 1},
            ],
            "delivery": DELIVERY,
        },
        headers=carol.headers,
    )

    assert response.status_code == 422
    assert "Home cleaning" in response.json()["message"]
    async with session_factory() as session:
        assert (await session.scalars(select(Order))).all() == []


# ── The phone number (README §7.5, X3 in part) ───────────────────────────


async def test_the_providers_phone_is_shown_only_while_they_have_a_subscription(
    db_client: AsyncClient, admin, market
) -> None:
    async def phone(product_id: str) -> str | None:
        return (await db_client.get(f"{API}/products/{product_id}")).json()["data"]["contact_phone"]

    assert await phone(market.cleaning) is None

    plan = await db_client.post(
        f"{API}/seller-plans",
        json={
            "code": "basic",
            "name": "Basic",
            "price": "10000",
            "duration_days": 30,
            "commission_rate": "7",
        },
        headers=admin.headers,
    )
    for seller in (market.pat, market.amina):
        assigned = await db_client.post(
            f"{API}/seller-subscriptions",
            json={"seller_id": seller.seller_id, "plan_id": plan.json()["data"]["id"]},
            headers=admin.headers,
        )
        assert assigned.status_code == 201, assigned.text

    assert await phone(market.cleaning) == BUSINESS_PHONE
    # Goods never show it: the rule is for services only.
    assert await phone(market.kettle) is None

    subscription = (
        await db_client.get(
            f"{API}/seller-subscriptions",
            params={"seller_id": market.pat.seller_id},
            headers=admin.headers,
        )
    ).json()["data"]["items"][0]
    cancelled = await db_client.post(
        f"{API}/seller-subscriptions/{subscription['id']}/cancel",
        json={"reason": "Payment bounced"},
        headers=admin.headers,
    )
    assert cancelled.status_code == 200, cancelled.text
    assert await phone(market.cleaning) is None


# ── Requesting ───────────────────────────────────────────────────────────


async def test_a_request_records_the_price_and_place_and_charges_nothing(
    db_client: AsyncClient, carol, market, requested, session_factory
) -> None:
    request = await requested()

    assert request["status"] == "requested"
    assert (request["service_name"], request["seller_name"]) == ("Home cleaning", "Pat Cleaning")
    assert (request["unit_price"], request["currency"]) == ("20000.00", "RWF")
    assert request["service_location"] == "at_customer"
    assert request["contact"] == CONTACT
    assert request["place"]["address"] == "KK 15 Ave, house 12"
    assert request["note"] == "Two bedrooms"
    assert request["order"] is None
    async with session_factory() as session:
        assert (await session.scalars(select(Order))).all() == []

    mine = await db_client.get(MY_REQUESTS, headers=carol.headers)
    incoming = await db_client.get(INCOMING, headers=market.pat.headers)
    assert [r["id"] for r in mine.json()["data"]["items"]] == [request["id"]]
    assert [r["id"] for r in incoming.json()["data"]["items"]] == [request["id"]]


@pytest.mark.parametrize(
    "scheduled_for",
    [
        (datetime.now(UTC) - timedelta(hours=1)).isoformat(),  # in the past
        datetime.now().replace(tzinfo=None).isoformat(),  # no time zone
    ],
)
async def test_the_time_must_be_in_the_future_with_a_time_zone(
    ask, market, scheduled_for: str
) -> None:
    assert (await ask(scheduled_for=scheduled_for)).status_code == 422


async def test_only_a_service_on_offer_can_be_requested_and_not_from_yourself(
    db_client: AsyncClient, market, ask, listing
) -> None:
    assert (await ask(service_id=market.kettle)).status_code == 422
    assert (await ask(service_id=str(uuid.uuid4()))).status_code == 404

    own = await db_client.post(
        REQUESTS,
        json={
            "service_id": market.cleaning,
            "scheduled_for": soon(),
            "contact": CONTACT,
            "place": PLACE,
        },
        headers=market.pat.headers,
    )
    assert own.status_code == 422

    await db_client.post(
        f"{API}/products/mine/{market.cleaning}/archive", headers=market.pat.headers
    )
    assert (await ask()).status_code == 404


async def test_requesting_needs_a_login(db_client: AsyncClient, market) -> None:
    response = await db_client.post(
        REQUESTS,
        json={
            "service_id": market.cleaning,
            "scheduled_for": soon(),
            "contact": CONTACT,
            "place": PLACE,
        },
    )
    assert response.status_code == 401


# ── Service details (README §7.5, V15–V18) ───────────────────────────────


async def test_a_service_is_published_only_with_all_its_details(
    db_client: AsyncClient, market
) -> None:
    category = await db_client.post(
        f"{API}/categories", json={"name": "Garden"}, headers=market.pat.headers
    )
    category_id = category.json()["data"]["id"]
    goods = await db_client.post(
        f"{API}/products",
        json={"name": "Rake", "price": "5000", "category_id": category_id, "service": CLEANING},
        headers=market.pat.headers,
    )
    assert goods.status_code == 422

    draft = await db_client.post(
        f"{API}/products",
        json={"kind": "service", "name": "Mowing", "price": "8000", "category_id": category_id},
        headers=market.pat.headers,
    )
    assert draft.status_code == 201, draft.text
    product_id = draft.json()["data"]["id"]
    await db_client.post(
        f"{API}/products/mine/{product_id}/images",
        files={"file": ("photo.jpg", JPEG)},
        headers=market.pat.headers,
    )
    blockers = draft.json()["data"]["publish_blockers"]
    assert "Say where the service is done" in blockers
    assert "Add the working hours" in blockers
    url = f"{API}/products/mine/{product_id}"
    assert (await db_client.post(f"{url}/publish", headers=market.pat.headers)).status_code == 422

    # At the buyer's place needs districts; districts mean nothing elsewhere.
    no_area = await db_client.patch(
        url, json={"service": {**CLEANING, "areas": []}}, headers=market.pat.headers
    )
    assert "Add at least one district you work in" in no_area.json()["data"]["publish_blockers"]
    wrong = await db_client.patch(
        url,
        json={"service": {**CLEANING, "location": "online"}},
        headers=market.pat.headers,
    )
    assert wrong.status_code == 422

    complete = await db_client.patch(url, json={"service": CLEANING}, headers=market.pat.headers)
    assert complete.json()["data"]["publish_blockers"] == []
    published = await db_client.post(f"{url}/publish", headers=market.pat.headers)
    assert published.status_code == 200, published.text
    service = (await db_client.get(f"{API}/products/{product_id}")).json()["data"]["service"]
    assert (service["location"], service["duration_minutes"]) == ("at_customer", 180)
    assert service["areas"] == ["Gasabo", "Kicukiro"]
    assert len(service["hours"]) == 7

    # A published service must stay complete.
    cleared = await db_client.patch(
        url, json={"service": {"hours": []}}, headers=market.pat.headers
    )
    assert cleared.status_code == 422


async def test_a_service_at_the_buyers_place_needs_a_place_it_covers(ask) -> None:
    assert (await ask(place=None)).status_code == 422
    elsewhere = await ask(place={**PLACE, "province": "South", "district": "Huye"})
    assert elsewhere.status_code == 422
    assert "Kicukiro" in elsewhere.json()["message"]
    # Districts match without regard to case.
    assert (await ask(place={**PLACE, "district": "kicukiro"})).status_code == 201


async def test_a_request_respects_the_notice_and_the_working_hours(
    db_client: AsyncClient, market, ask
) -> None:
    await db_client.patch(
        f"{API}/products/mine/{market.cleaning}",
        json={"service": {"min_notice_hours": 48}},
        headers=market.pat.headers,
    )

    too_soon = await ask(scheduled_for=soon(days=1))
    after_hours = await ask(scheduled_for=soon(hour=19))
    early_morning = await ask(scheduled_for=soon(hour=7))

    assert too_soon.status_code == 422
    assert "48 hours" in too_soon.json()["message"]
    assert after_hours.status_code == 422
    assert "working hours" in after_hours.json()["message"]
    assert early_morning.status_code == 422
    assert (await ask(scheduled_for=soon(hour=17))).status_code == 201


async def test_at_the_providers_place_the_buyer_learns_the_address_once_paid(
    db_client: AsyncClient, carol, market, listing, ask, pay
) -> None:
    salon = await listing(
        market.pat,
        "Haircut",
        "6000",
        "service",
        {**CLEANING, "location": "at_provider", "areas": []},
    )
    public = (await db_client.get(f"{API}/products/{salon}")).json()["data"]
    assert public["provider_area"] == {
        "province": "Kigali",
        "district": "Gasabo",
        "sector": "Remera",
    }

    assert (await ask(service_id=salon)).status_code == 422  # no place to give
    response = await ask(service_id=salon, place=None)
    assert response.status_code == 201, response.text
    request = response.json()["data"]
    assert (request["service_location"], request["place"]) == ("at_provider", None)

    accepted = await db_client.post(
        f"{INCOMING}/{request['id']}/accept", headers=market.pat.headers
    )
    assert accepted.status_code == 200, accepted.text
    order_id = accepted.json()["data"]["order"]["id"]
    order_url = f"{API}/orders/mine/{order_id}"
    unpaid = (await db_client.get(order_url, headers=carol.headers)).json()["data"]
    assert unpaid["service_location"] == "at_provider"
    assert unpaid["delivery"]["district"] is None
    assert unpaid["seller_orders"][0]["provider_address"] is None

    await pay(order_id)
    part = (await db_client.get(order_url, headers=carol.headers)).json()["data"]["seller_orders"][
        0
    ]
    assert part["provider_address"] == {
        "province": "Kigali",
        "district": "Gasabo",
        "sector": "Remera",
        "street_address": None,
    }
    assert part["provider_phone"] == BUSINESS_PHONE


async def test_an_online_service_takes_no_place(market, listing, ask) -> None:
    lessons = await listing(
        market.pat,
        "Maths lessons",
        "5000",
        "service",
        {**CLEANING, "location": "online", "areas": []},
    )

    assert (await ask(service_id=lessons)).status_code == 422
    response = await ask(service_id=lessons, place=None)
    assert response.status_code == 201, response.text
    assert response.json()["data"]["place"] is None


async def test_buyers_find_the_services_they_can_get_in_their_district(
    db_client: AsyncClient, market, listing
) -> None:
    # Cleaning comes to Kicukiro and Gasabo; the salon is in Gasabo; lessons are online.
    await listing(
        market.pat,
        "Haircut",
        "6000",
        "service",
        {**CLEANING, "location": "at_provider", "areas": []},
    )
    await listing(
        market.amina,
        "Maths lessons",
        "5000",
        "service",
        {**CLEANING, "location": "online", "areas": []},
    )

    async def names(district: str) -> set[str]:
        page = await db_client.get(
            f"{API}/products", params={"kind": "service", "district": district}
        )
        assert page.status_code == 200, page.text
        return {item["name"] for item in page.json()["data"]["items"]}

    assert await names("Huye") == {"Maths lessons"}
    assert await names("kicukiro") == {"Home cleaning", "Maths lessons"}
    assert await names("Gasabo") == {"Home cleaning", "Haircut", "Maths lessons"}
    goods = await db_client.get(f"{API}/products", params={"district": "Gasabo"})
    assert goods.status_code == 422


# ── Answering ────────────────────────────────────────────────────────────


async def test_accepting_creates_the_order_at_the_requested_price(
    db_client: AsyncClient, carol, market, requested, session_factory
) -> None:
    request = await requested()
    # Pat raises the price after Carol asked: Carol still pays what she saw.
    await db_client.patch(
        f"{API}/products/mine/{market.cleaning}",
        json={"price": "30000"},
        headers=market.pat.headers,
    )

    response = await db_client.post(
        f"{INCOMING}/{request['id']}/accept", headers=market.pat.headers
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["status"] == "accepted"
    assert data["responded_at"] is not None
    order = data["order"]
    assert (order["kind"], order["status"], order["total_amount"]) == (
        "service",
        "awaiting_payment",
        "20000.00",
    )
    assert datetime.fromisoformat(order["scheduled_for"]) == datetime.fromisoformat(
        request["scheduled_for"]
    )

    async with session_factory() as session:
        stored = await session.get(ServiceRequest, uuid.UUID(request["id"]))
        assert str(stored.order_id) == order["id"]
    part = await seller_order_of(session_factory, order["id"])
    assert (part.subtotal, part.commission_rate) == (Decimal("20000.00"), Decimal("10.00"))
    assert (part.commission_amount, part.seller_amount) == (Decimal("2000.00"), Decimal("18000.00"))
    assert part.status == "awaiting_payment"

    # The buyer sees it among their orders, with where and when.
    mine = await db_client.get(f"{API}/orders/mine/{order['id']}", headers=carol.headers)
    assert mine.json()["data"]["delivery"]["address"] == "KK 15 Ave, house 12"
    # The provider does not see it among shop orders until it is paid.
    shop = await db_client.get(SHOP_ORDERS, headers=market.pat.headers)
    assert shop.json()["data"]["total"] == 0


async def test_declining_needs_a_reason_and_creates_no_order(
    db_client: AsyncClient, market, requested, session_factory
) -> None:
    request = await requested()
    url = f"{INCOMING}/{request['id']}/decline"

    assert (await db_client.post(url, json={}, headers=market.pat.headers)).status_code == 422
    declined = await db_client.post(
        url, json={"reason": "Fully booked that week"}, headers=market.pat.headers
    )

    assert declined.status_code == 200, declined.text
    data = declined.json()["data"]
    assert (data["status"], data["status_reason"], data["order"]) == (
        "declined",
        "Fully booked that week",
        None,
    )
    late = await db_client.post(f"{INCOMING}/{request['id']}/accept", headers=market.pat.headers)
    assert late.status_code == 409
    async with session_factory() as session:
        assert (await session.scalars(select(Order))).all() == []


async def test_the_buyer_can_cancel_only_before_an_answer(
    db_client: AsyncClient, carol, market, requested, accepted
) -> None:
    request = await requested()
    cancelled = await db_client.post(
        f"{MY_REQUESTS}/{request['id']}/cancel",
        json={"reason": "Found someone else"},
        headers=carol.headers,
    )
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["data"]["status"] == "cancelled"
    too_late = await db_client.post(
        f"{INCOMING}/{request['id']}/accept", headers=market.pat.headers
    )
    assert too_late.status_code == 409

    # Once accepted, the request is answered; the unpaid ORDER is what the
    # buyer cancels.
    answered = await accepted()
    refused = await db_client.post(
        f"{MY_REQUESTS}/{answered['id']}/cancel", json={}, headers=carol.headers
    )
    assert refused.status_code == 409
    order_cancel = await db_client.post(
        f"{API}/orders/mine/{answered['order']['id']}/cancel", json={}, headers=carol.headers
    )
    assert order_cancel.status_code == 200, order_cancel.text
    after = await db_client.get(f"{MY_REQUESTS}/{answered['id']}", headers=carol.headers)
    assert after.json()["data"]["order"]["status"] == "cancelled"


async def test_a_request_cannot_be_accepted_once_its_time_has_passed(
    db_client: AsyncClient, market, requested, monkeypatch
) -> None:
    request = await requested()
    later = datetime.now(UTC) + timedelta(days=10)
    monkeypatch.setattr(service_request_service, "utc_now", lambda: later)

    response = await db_client.post(
        f"{INCOMING}/{request['id']}/accept", headers=market.pat.headers
    )

    assert response.status_code == 422
    assert "passed" in response.json()["message"]


async def test_a_service_taken_off_offer_cannot_be_accepted(
    db_client: AsyncClient, admin, market, requested
) -> None:
    request = await requested()
    hidden = await db_client.post(
        f"{API}/products/moderation/{market.cleaning}/hide", headers=admin.headers
    )
    assert hidden.status_code == 200, hidden.text

    response = await db_client.post(
        f"{INCOMING}/{request['id']}/accept", headers=market.pat.headers
    )

    assert response.status_code == 422
    still = await db_client.get(f"{INCOMING}/{request['id']}", headers=market.pat.headers)
    assert still.json()["data"]["status"] == "requested"


# ── After payment: done, confirmed, settled ──────────────────────────────


async def test_a_paid_service_goes_straight_to_work_and_settles_on_confirmation(
    db_client: AsyncClient, carol, market, paid, session_factory
) -> None:
    request, part_id = await paid()

    part = await db_client.get(f"{SHOP_ORDERS}/{part_id}", headers=market.pat.headers)
    assert (part.json()["data"]["kind"], part.json()["data"]["status"]) == ("service", "accepted")
    assert await wallet(db_client, market.pat) == ("18000.00", "0.00")

    # Goods steps do not apply to a service.
    for step in ("accept", "ship", "deliver"):
        refused = await db_client.post(
            f"{SHOP_ORDERS}/{part_id}/{step}", headers=market.pat.headers
        )
        assert refused.status_code == 409, step

    order_id = request["order"]["id"]
    confirm = f"{API}/orders/mine/{order_id}/seller-orders/{part_id}/confirm-receipt"
    early = await db_client.post(confirm, headers=carol.headers)
    assert early.status_code == 409

    done = await db_client.post(f"{SHOP_ORDERS}/{part_id}/mark-done", headers=market.pat.headers)
    assert done.status_code == 200, done.text
    assert done.json()["data"]["status"] == "delivered"

    confirmed = await db_client.post(confirm, headers=carol.headers)
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["data"]["status"] == "completed"
    assert await wallet(db_client, market.pat) == ("0.00", "18000.00")
    stored = await seller_order_of(session_factory, order_id)
    assert stored.status == "completed"


async def test_the_buyer_gets_the_providers_phone_once_the_service_is_paid(
    db_client: AsyncClient, carol, market, accepted, pay
) -> None:
    # Pat has no subscription: the phone is not on the listing...
    listing = await db_client.get(f"{API}/products/{market.cleaning}")
    assert listing.json()["data"]["contact_phone"] is None

    request = await accepted()
    order_url = f"{API}/orders/mine/{request['order']['id']}"

    # ...nor on the order while it is unpaid,
    unpaid = await db_client.get(order_url, headers=carol.headers)
    assert unpaid.json()["data"]["seller_orders"][0]["provider_phone"] is None

    # but it is once the buyer has paid, whatever the subscription.
    await pay(request["order"]["id"])
    paid = await db_client.get(order_url, headers=carol.headers)
    assert paid.json()["data"]["seller_orders"][0]["provider_phone"] == BUSINESS_PHONE


async def test_a_paid_goods_order_never_shows_the_sellers_phone(
    db_client: AsyncClient, carol, market, pay
) -> None:
    placed = await db_client.post(
        f"{API}/orders",
        json={
            "items": [{"product_id": market.kettle, "quantity": 1}],
            "delivery": DELIVERY,
        },
        headers=carol.headers,
    )
    order_id = placed.json()["data"]["id"]
    await pay(order_id)

    order = await db_client.get(f"{API}/orders/mine/{order_id}", headers=carol.headers)

    assert order.json()["data"]["seller_orders"][0]["provider_phone"] is None


async def test_mark_done_is_for_services_only(db_client: AsyncClient, carol, market, pay) -> None:
    placed = await db_client.post(
        f"{API}/orders",
        json={
            "items": [{"product_id": market.kettle, "quantity": 1}],
            "delivery": DELIVERY,
        },
        headers=carol.headers,
    )
    order_id = placed.json()["data"]["id"]
    await pay(order_id)
    part_id = placed.json()["data"]["seller_orders"][0]["id"]
    await db_client.post(f"{SHOP_ORDERS}/{part_id}/accept", headers=market.amina.headers)

    response = await db_client.post(
        f"{SHOP_ORDERS}/{part_id}/mark-done", headers=market.amina.headers
    )

    assert response.status_code == 409


async def test_a_provider_who_cannot_do_a_paid_service_cancels_and_the_earning_is_reversed(
    db_client: AsyncClient, carol, market, paid
) -> None:
    request, part_id = await paid()

    no_reason = await db_client.post(
        f"{SHOP_ORDERS}/{part_id}/reject", json={}, headers=market.pat.headers
    )
    rejected = await db_client.post(
        f"{SHOP_ORDERS}/{part_id}/reject",
        json={"reason": "Our cleaner is ill"},
        headers=market.pat.headers,
    )

    assert no_reason.status_code == 422
    assert rejected.status_code == 200, rejected.text
    assert rejected.json()["data"]["status"] == "rejected"
    assert await wallet(db_client, market.pat) == ("0.00", "0.00")
    order = await db_client.get(
        f"{API}/orders/mine/{request['order']['id']}", headers=carol.headers
    )
    assert order.json()["data"]["status"] == "cancelled"
    assert order.json()["data"]["seller_orders"][0]["status_reason"] == "Our cleaner is ill"


# ── Who sees what ────────────────────────────────────────────────────────


async def test_requests_are_visible_only_to_their_buyer_provider_and_staff(
    db_client: AsyncClient, admin, user, market, requested
) -> None:
    request = await requested()
    rid = request["id"]

    # Another buyer, and another shop, see nothing.
    assert (await db_client.get(f"{MY_REQUESTS}/{rid}", headers=user.headers)).status_code == 404
    assert (
        await db_client.get(f"{INCOMING}/{rid}", headers=market.amina.headers)
    ).status_code == 404
    assert (
        await db_client.post(f"{INCOMING}/{rid}/accept", headers=market.amina.headers)
    ).status_code == 404
    # An account that is not a seller cannot answer requests at all.
    assert (await db_client.get(INCOMING, headers=user.headers)).status_code == 403
    # Staff endpoints are closed to sellers and open to admins.
    assert (await db_client.get(REQUESTS, headers=market.pat.headers)).status_code == 403
    everything = await db_client.get(
        REQUESTS, params={"seller_id": market.pat.seller_id}, headers=admin.headers
    )
    assert [r["id"] for r in everything.json()["data"]["items"]] == [rid]
    assert (await db_client.get(f"{REQUESTS}/{rid}", headers=admin.headers)).status_code == 200


async def test_the_database_refuses_an_accepted_request_without_an_order(
    market, requested, session_factory
) -> None:
    request = await requested()

    async with session_factory() as session:
        with pytest.raises(IntegrityError):
            await session.execute(
                update(ServiceRequest)
                .where(ServiceRequest.id == uuid.UUID(request["id"]))
                .values(status="accepted")
            )
