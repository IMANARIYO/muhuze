"""A shop with money in its wallet, reachable through the HTTP API, for the
withdrawals tests. Money is driven the way it is in production: a buyer pays,
staff approve, the seller delivers, the buyer confirms — then the seller's
earnings are available to withdraw.
"""

import pytest
from httpx import AsyncClient

API = "/api/v1"
JPEG = b"\xff\xd8\xff\xe0" + b"jpeg-bytes" * 20
DELIVERY = {
    "recipient_name": "Ophelia Umuhoza",
    "recipient_phone": "+250788999000",
    "province": "Kigali",
    "district": "Kicukiro",
    "sector": "Niboye",
}
DESTINATION = {
    "type": "mobile_money",
    "provider": "MTN MoMo",
    "account_number": "0788123456",
    "account_name": "LAURA WAREHOUSE",
}


@pytest.fixture
async def shop(db_client: AsyncClient, sign_up, open_shop):
    """Laura: an approved, active seller with one product at 150,000."""
    seller = await sign_up("laura@example.com")
    seller.seller_id = await open_shop(seller, "Laura Shop")
    category = await db_client.post(
        f"{API}/categories", json={"name": "Things"}, headers=seller.headers
    )
    created = await db_client.post(
        f"{API}/products",
        json={
            "name": "Item",
            "price": "150000",
            "category_id": category.json()["data"]["id"],
        },
        headers=seller.headers,
    )
    seller.product_id = created.json()["data"]["id"]
    await db_client.post(
        f"{API}/products/mine/{seller.product_id}/images",
        files={"file": ("photo.jpg", JPEG)},
        headers=seller.headers,
    )
    published = await db_client.post(
        f"{API}/products/mine/{seller.product_id}/publish", headers=seller.headers
    )
    assert published.status_code == 200, published.text
    return seller


@pytest.fixture
async def market(db_client: AsyncClient, admin, shop):
    """MUHUZE ready to trade: a 10% default commission and a payment
    destination to be paid on."""
    rate = await db_client.post(
        f"{API}/commission-rates/default", json={"rate": "10"}, headers=admin.headers
    )
    assert rate.status_code == 201, rate.text
    destination = await db_client.post(
        f"{API}/payment-destinations",
        json={
            "method": "mobile_money",
            "provider": "Example Mobile Money",
            "account_reference": "0780000002",
            "registered_name": "MUHUZE EXAMPLE LTD",
        },
        headers=admin.headers,
    )

    class Market:
        destination_id = destination.json()["data"]["id"]

    Market.shop = shop
    return Market


@pytest.fixture
async def ophelia(sign_up):
    return await sign_up("ophelia@example.com")


@pytest.fixture
def buy(db_client: AsyncClient, ophelia):
    async def _buy(shop, quantity: int = 1) -> dict:
        response = await db_client.post(
            f"{API}/orders",
            json={
                "items": [{"product_id": shop.product_id, "quantity": quantity}],
                "delivery": DELIVERY,
            },
            headers=ophelia.headers,
        )
        assert response.status_code == 201, response.text
        return response.json()["data"]

    return _buy


@pytest.fixture
def pay(db_client: AsyncClient, admin, ophelia, market):
    """The buyer submits a payment and staff approve it."""
    counter = iter(range(1, 1000))

    async def _pay(order: dict) -> str:
        submitted = await db_client.post(
            f"{API}/orders/mine/{order['id']}/payment",
            json={
                "destination_id": market.destination_id,
                "reference": f"WD-{next(counter):04d}",
                "payer_name": "Ophelia",
            },
            headers=ophelia.headers,
        )
        assert submitted.status_code == 201, submitted.text
        payment_id = submitted.json()["data"]["id"]
        approved = await db_client.post(
            f"{API}/payments/{payment_id}/approve", headers=admin.headers
        )
        assert approved.status_code == 200, approved.text
        return payment_id

    return _pay


@pytest.fixture
def add_destination(db_client: AsyncClient):
    """Register a payout destination for a seller. Returns the created row."""

    async def _add(seller, **overrides) -> dict:
        payload = dict(DESTINATION)
        payload.update(overrides)
        response = await db_client.post(
            f"{API}/withdrawal/destinations", json=payload, headers=seller.headers
        )
        assert response.status_code == 201, response.text
        return response.json()["data"]

    return _add


@pytest.fixture
async def earnings(db_client: AsyncClient, market, ophelia, buy, pay):
    """Three paid units, one settled and two pending: Laura has 135,000.00
    available and 270,000.00 still pending. Returns the settled order."""
    orders = [await buy(market.shop, 1) for _ in range(3)]
    for order in orders:
        await pay(order)
    await settle(db_client, orders[0], part_id(orders[0], "Laura Shop"), market.shop, ophelia)
    return orders[0]


async def deliver(db_client: AsyncClient, seller, seller_order_id: str) -> None:
    for step in ("accept", "ship"):
        response = await db_client.post(
            f"{API}/seller-orders/mine/{seller_order_id}/{step}", headers=seller.headers
        )
        assert response.status_code == 200, response.text


async def settle(db_client: AsyncClient, order: dict, seller_order_id: str, seller, buyer) -> None:
    """Deliver and have the buyer confirm receipt: the earning becomes available."""
    await deliver(db_client, seller, seller_order_id)
    confirmed = await db_client.post(
        f"{API}/orders/mine/{order['id']}/seller-orders/{seller_order_id}/confirm-receipt",
        headers=buyer.headers,
    )
    assert confirmed.status_code == 200, confirmed.text


def part_id(order: dict, shop_name: str) -> str:
    return next(p["id"] for p in order["seller_orders"] if p["seller_name"] == shop_name)


async def wallet(db_client: AsyncClient, seller) -> tuple[str, str]:
    """(available_balance, total_withdrawn) as strings."""
    data = (await db_client.get(f"{API}/wallet/mine", headers=seller.headers)).json()["data"]
    return data["available_balance"], data["total_withdrawn"]


async def ask_for(db_client: AsyncClient, seller, *, amount: str, destination_id: str) -> object:
    return await db_client.post(
        f"{API}/withdrawals",
        json={"amount": amount, "payout_destination_id": destination_id},
        headers=seller.headers,
    )


async def movements(db_client: AsyncClient, seller) -> list[dict]:
    data = (await db_client.get(f"{API}/wallet/mine/transactions", headers=seller.headers)).json()
    return data["data"]["items"]
