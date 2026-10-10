"""Revenue records and seller wallets, through the HTTP API and against a
real PostgreSQL database.

Money is driven the way it is in production: a buyer places an order,
submits a payment, staff approve it, sellers fulfil, the buyer confirms.
The tests assert what is PERSISTED, and map to the financial invariants of
README §14.
"""

import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from app.modules.wallets.wallet_exceptions import (
    EarningAlreadySettledError,
    EarningNotRecordedError,
    EarningReversedError,
)
from app.modules.wallets.wallet_model import RevenueTransaction, Wallet, WalletTransaction
from app.modules.wallets.wallet_service import WalletService

API = "/api/v1"
MY_WALLET = f"{API}/wallet/mine"
JPEG = b"\xff\xd8\xff\xe0" + b"jpeg-bytes" * 20
DELIVERY = {
    "recipient_name": "Carol Mukamana",
    "recipient_phone": "+250788999000",
    "province": "Kigali",
    "district": "Kicukiro",
    "sector": "Niboye",
}


@pytest.fixture
def make_shop(db_client: AsyncClient, sign_up, open_shop):
    """A shop with one product on sale. Returns the seller, with ids attached."""

    async def _make_shop(email: str, name: str, price: str):
        seller = await sign_up(email)
        seller.seller_id = await open_shop(seller, name)
        category = await db_client.post(
            f"{API}/categories", json={"name": "Things"}, headers=seller.headers
        )
        created = await db_client.post(
            f"{API}/products",
            json={"name": "Item", "price": price, "category_id": category.json()["data"]["id"]},
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

    return _make_shop


@pytest.fixture
async def market(db_client: AsyncClient, admin, make_shop):
    """MUHUZE ready to trade: a 10% default commission and an account to be
    paid on. Amina sells at 104,999.99 and Brian at 450,000."""
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

    class Market:
        destination_id = destination.json()["data"]["id"]

    Market.amina = await make_shop("amina@example.com", "Amina Shop", "104999.99")
    Market.brian = await make_shop("brian@example.com", "Brian Shop", "450000")
    return Market


@pytest.fixture
async def carol(sign_up):
    return await sign_up("carol@example.com")


@pytest.fixture
def buy(db_client: AsyncClient, carol):
    async def _buy(*items: tuple[object, int]) -> dict:
        response = await db_client.post(
            f"{API}/orders",
            json={
                "items": [{"product_id": shop.product_id, "quantity": q} for shop, q in items],
                "delivery": DELIVERY,
            },
            headers=carol.headers,
        )
        assert response.status_code == 201, response.text
        return response.json()["data"]

    return _buy


@pytest.fixture
def pay(db_client: AsyncClient, admin, carol, market):
    """The buyer submits a payment and staff approve it. Returns the payment id."""
    counter = iter(range(1, 1000))

    async def _pay(order: dict) -> str:
        submitted = await db_client.post(
            f"{API}/orders/mine/{order['id']}/payment",
            json={
                "destination_id": market.destination_id,
                "reference": f"MP-{next(counter):04d}",
                "payer_name": "Carol",
            },
            headers=carol.headers,
        )
        assert submitted.status_code == 201, submitted.text
        payment_id = submitted.json()["data"]["id"]
        approved = await db_client.post(
            f"{API}/payments/{payment_id}/approve", headers=admin.headers
        )
        assert approved.status_code == 200, approved.text
        return payment_id

    return _pay


def part_id(order: dict, shop_name: str) -> str:
    return next(p["id"] for p in order["seller_orders"] if p["seller_name"] == shop_name)


async def balances(db_client: AsyncClient, seller) -> tuple[str, str, str]:
    """(pending, available, total earned)"""
    data = (await db_client.get(MY_WALLET, headers=seller.headers)).json()["data"]
    return data["pending_balance"], data["available_balance"], data["total_earned"]


async def deliver(db_client: AsyncClient, seller, seller_order_id: str) -> None:
    for step in ("accept", "ship"):
        response = await db_client.post(
            f"{API}/seller-orders/mine/{seller_order_id}/{step}", headers=seller.headers
        )
        assert response.status_code == 200, response.text


# ── Earning, settlement ──────────────────────────────────────────────────


async def test_a_seller_without_sales_has_an_empty_wallet(db_client: AsyncClient, market) -> None:
    response = await db_client.get(MY_WALLET, headers=market.amina.headers)

    assert response.status_code == 200
    assert response.json()["data"] == {
        "seller_id": market.amina.seller_id,
        "currency": "RWF",
        "pending_balance": "0.00",
        "available_balance": "0.00",
        "total_earned": "0.00",
        "total_withdrawn": "0.00",
    }
    movements = await db_client.get(f"{MY_WALLET}/transactions", headers=market.amina.headers)
    assert movements.json()["data"]["total"] == 0


async def test_nothing_is_earned_until_the_payment_is_confirmed(
    db_client: AsyncClient, carol, market, buy
) -> None:
    order = await buy((market.amina, 1))
    await db_client.post(
        f"{API}/orders/mine/{order['id']}/payment",
        json={"destination_id": market.destination_id, "reference": "MP-1", "payer_name": "Carol"},
        headers=carol.headers,
    )

    # Placed, and the buyer says they paid: still nothing (README §12.7).
    assert await balances(db_client, market.amina) == ("0.00", "0.00", "0.00")


async def test_a_confirmed_payment_credits_each_seller_as_pending(
    db_client: AsyncClient, market, buy, pay
) -> None:
    order = await buy((market.amina, 1), (market.brian, 1))

    await pay(order)

    # 10% commission each: 104999.99 → 10500.00 + 94499.99; 450000 → 45000 + 405000.
    assert await balances(db_client, market.amina) == ("94499.99", "0.00", "94499.99")
    assert await balances(db_client, market.brian) == ("405000.00", "0.00", "405000.00")
    movements = await db_client.get(f"{MY_WALLET}/transactions", headers=market.amina.headers)
    (earning,) = movements.json()["data"]["items"]
    assert earning["kind"] == "earning"
    assert (earning["pending_change"], earning["available_change"]) == ("94499.99", "0.00")
    assert (earning["pending_after"], earning["available_after"]) == ("94499.99", "0.00")
    assert earning["order_id"] == order["id"]
    assert earning["seller_order_id"] == part_id(order, "Amina Shop")


async def test_an_earning_becomes_available_when_the_buyer_confirms_receipt(
    db_client: AsyncClient, carol, market, buy, pay
) -> None:
    order = await buy((market.amina, 1), (market.brian, 1))
    await pay(order)
    amina_part = part_id(order, "Amina Shop")

    await deliver(db_client, market.amina, amina_part)
    # Shipped is not enough: the money stays pending until the buyer has it.
    assert await balances(db_client, market.amina) == ("94499.99", "0.00", "94499.99")

    confirmed = await db_client.post(
        f"{API}/orders/mine/{order['id']}/seller-orders/{amina_part}/confirm-receipt",
        headers=carol.headers,
    )

    assert confirmed.status_code == 200
    assert await balances(db_client, market.amina) == ("0.00", "94499.99", "94499.99")
    # Only that seller's part settles; the other shop is unaffected.
    assert await balances(db_client, market.brian) == ("405000.00", "0.00", "405000.00")
    movements = await db_client.get(f"{MY_WALLET}/transactions", headers=market.amina.headers)
    assert [
        (
            m["kind"],
            m["pending_change"],
            m["available_change"],
            m["pending_after"],
            m["available_after"],
        )
        for m in movements.json()["data"]["items"]
    ] == [
        ("settlement", "-94499.99", "94499.99", "0.00", "94499.99"),  # newest first
        ("earning", "94499.99", "0.00", "94499.99", "0.00"),
    ]


async def test_sales_add_up_in_one_wallet(db_client: AsyncClient, carol, market, buy, pay) -> None:
    first, second = await buy((market.brian, 1)), await buy((market.brian, 2))
    await pay(first)
    await pay(second)
    first_part = part_id(first, "Brian Shop")
    await deliver(db_client, market.brian, first_part)
    await db_client.post(
        f"{API}/orders/mine/{first['id']}/seller-orders/{first_part}/confirm-receipt",
        headers=carol.headers,
    )

    # 405000 available from the first; 810000 still pending from the second.
    assert await balances(db_client, market.brian) == ("810000.00", "405000.00", "1215000.00")


# ── Invariants (README §14) ──────────────────────────────────────────────


async def test_confirming_a_payment_twice_credits_once(
    db_client: AsyncClient, admin, market, buy, pay, session_factory
) -> None:
    order = await buy((market.amina, 1), (market.brian, 1))
    payment_id = await pay(order)

    for _ in range(3):  # a double click, a retry, a provider repeating itself
        again = await db_client.post(f"{API}/payments/{payment_id}/approve", headers=admin.headers)
        assert again.status_code == 200

    # Invariants 1–3: one revenue record per seller order, one credit per earning.
    assert await balances(db_client, market.amina) == ("94499.99", "0.00", "94499.99")
    async with session_factory() as session:
        revenue = list(await session.scalars(select(RevenueTransaction)))
        movements = list(await session.scalars(select(WalletTransaction)))
    assert len(revenue) == 2
    assert [m.kind for m in movements] == ["earning", "earning"]


async def test_the_database_itself_refuses_a_second_revenue_record_or_credit(
    market, buy, pay, session_factory
) -> None:
    await pay(await buy((market.amina, 1)))

    async with session_factory() as session:
        with pytest.raises(IntegrityError, match="uq_revenue_transactions_seller_order_id"):
            await session.execute(
                text(
                    "INSERT INTO revenue_transactions (id, seller_order_id, order_id, seller_id,"
                    " gross_amount, commission_rate, commission_amount, seller_amount, currency)"
                    " SELECT gen_random_uuid(), seller_order_id, order_id, seller_id, gross_amount,"
                    " commission_rate, commission_amount, seller_amount, currency"
                    " FROM revenue_transactions"
                )
            )
    async with session_factory() as session:
        with pytest.raises(IntegrityError, match="uq_wallet_transactions_revenue_transaction_id"):
            await session.execute(
                text(
                    "INSERT INTO wallet_transactions (id, wallet_id, kind, pending_change,"
                    " available_change, pending_after, available_after, revenue_transaction_id)"
                    " SELECT gen_random_uuid(), wallet_id, kind, pending_change, available_change,"
                    " pending_after, available_after, revenue_transaction_id"
                    " FROM wallet_transactions"
                )
            )


async def test_a_multi_seller_payment_reconciles_exactly(
    db_client: AsyncClient, admin, market, buy, pay
) -> None:
    order = await buy((market.amina, 3), (market.brian, 2))
    await pay(order)

    records = await db_client.get(
        f"{API}/revenue", params={"order_id": order["id"]}, headers=admin.headers
    )

    rows = records.json()["data"]["items"]
    assert len(rows) == 2
    # Invariant 13: Σ (seller earning + MUHUZE commission) = the payment amount.
    total = sum(Decimal(r["seller_amount"]) + Decimal(r["commission_amount"]) for r in rows)
    assert total == Decimal(order["total_amount"]) == Decimal("1214999.97")
    for row in rows:
        assert Decimal(row["seller_amount"]) + Decimal(row["commission_amount"]) == Decimal(
            row["gross_amount"]
        )


async def test_balances_always_equal_the_sum_of_their_movements(
    db_client: AsyncClient, carol, market, buy, pay, session_factory
) -> None:
    first, second, third = [await buy((market.amina, n)) for n in (1, 2, 3)]
    for order in (first, second, third):
        await pay(order)
    part = part_id(first, "Amina Shop")
    await deliver(db_client, market.amina, part)
    await db_client.post(
        f"{API}/orders/mine/{first['id']}/seller-orders/{part}/confirm-receipt",
        headers=carol.headers,
    )
    await db_client.post(
        f"{API}/seller-orders/mine/{part_id(second, 'Amina Shop')}/reject",
        json={"reason": "Ran out of stock"},
        headers=market.amina.headers,
    )

    # Invariant 8, three ways: the service's own check, the stored rows, and the API.
    async with session_factory() as session:
        assert await WalletService(session).reconcile(uuid.UUID(market.amina.seller_id)) is True
        wallet = await session.scalar(select(Wallet))
        movements = list(await session.scalars(select(WalletTransaction)))
    assert wallet.pending_balance == sum(m.pending_change for m in movements)
    assert wallet.available_balance == sum(m.available_change for m in movements)
    # 1 unit available, 2 units reversed, 3 units pending.
    assert await balances(db_client, market.amina) == ("283499.97", "94499.99", "377999.96")


async def test_an_earning_uses_the_terms_frozen_on_the_order(
    db_client: AsyncClient, admin, market, buy, pay
) -> None:
    order = await buy((market.brian, 1))  # placed at the 10% default

    # Before it is paid, MUHUZE raises its rate and Brian gets a 0% plan.
    await db_client.post(
        f"{API}/commission-rates/default", json={"rate": "30"}, headers=admin.headers
    )
    plan = await db_client.post(
        f"{API}/seller-plans",
        json={
            "code": "partner",
            "name": "Partner",
            "price": "100000",
            "duration_days": 30,
            "commission_rate": "0",
        },
        headers=admin.headers,
    )
    await db_client.post(
        f"{API}/seller-subscriptions",
        json={"seller_id": market.brian.seller_id, "plan_id": plan.json()["data"]["id"]},
        headers=admin.headers,
    )
    await pay(order)

    # Invariant 4: the order's own 10% applies, not 30% and not 0%.
    assert await balances(db_client, market.brian) == ("405000.00", "0.00", "405000.00")
    # A new order uses the plan in force now.
    await pay(await buy((market.brian, 1)))
    assert await balances(db_client, market.brian) == ("855000.00", "0.00", "855000.00")


async def test_the_database_refuses_a_negative_balance(market, buy, pay, session_factory) -> None:
    await pay(await buy((market.amina, 1)))

    async with session_factory() as session:
        with pytest.raises(IntegrityError, match="ck_wallets_balances_not_negative"):
            await session.execute(text("UPDATE wallets SET pending_balance = -0.01"))


# ── Reversal ─────────────────────────────────────────────────────────────


async def test_rejecting_a_paid_order_reverses_the_earning_with_a_new_record(
    db_client: AsyncClient, admin, market, buy, pay, session_factory
) -> None:
    order = await buy((market.amina, 1), (market.brian, 1))
    await pay(order)

    rejected = await db_client.post(
        f"{API}/seller-orders/mine/{part_id(order, 'Brian Shop')}/reject",
        json={"reason": "Sold the last one yesterday"},
        headers=market.brian.headers,
    )

    assert rejected.status_code == 200
    assert await balances(db_client, market.brian) == ("0.00", "0.00", "0.00")
    assert await balances(db_client, market.amina) == ("94499.99", "0.00", "94499.99")  # untouched
    # Invariant 12: nothing was deleted or edited; a compensating movement was added.
    movements = await db_client.get(f"{MY_WALLET}/transactions", headers=market.brian.headers)
    assert [(m["kind"], m["pending_change"]) for m in movements.json()["data"]["items"]] == [
        ("reversal", "-405000.00"),
        ("earning", "405000.00"),
    ]
    async with session_factory() as session:
        revenue = await session.scalar(
            select(RevenueTransaction).where(
                RevenueTransaction.seller_id == uuid.UUID(market.brian.seller_id)
            )
        )
    assert revenue.reversed_at is not None
    assert revenue.seller_amount == Decimal("405000.00")  # the original amounts stay
    # A reversed sale is no longer counted as revenue.
    summary = await db_client.get(
        f"{API}/revenue/summary",
        params={"seller_id": market.brian.seller_id},
        headers=admin.headers,
    )
    assert summary.json()["data"] == {
        "sales": 0,
        "gross_amount": "0.00",
        "commission_amount": "0.00",
        "seller_amount": "0.00",
        "currency": "RWF",
    }


async def test_the_ledger_acts_once_and_refuses_what_makes_no_sense(
    db_client: AsyncClient, carol, market, buy, pay, session_factory
) -> None:
    settled, reversed_, never_paid = [await buy((market.amina, 1)) for _ in range(3)]
    await pay(settled)
    await pay(reversed_)
    settled_part, reversed_part = part_id(settled, "Amina Shop"), part_id(reversed_, "Amina Shop")
    await deliver(db_client, market.amina, settled_part)
    await db_client.post(
        f"{API}/orders/mine/{settled['id']}/seller-orders/{settled_part}/confirm-receipt",
        headers=carol.headers,
    )
    await db_client.post(
        f"{API}/seller-orders/mine/{reversed_part}/reject",
        json={"reason": "Ran out of stock"},
        headers=market.amina.headers,
    )
    before = await balances(db_client, market.amina)

    async with session_factory() as session:
        ledger = WalletService(session)
        # Repeats change nothing (invariant 3).
        await ledger.settle(uuid.UUID(settled_part))
        await ledger.reverse(uuid.UUID(reversed_part))
        # A released earning cannot be reversed here, nor a reversed one released.
        with pytest.raises(EarningAlreadySettledError):
            await ledger.reverse(uuid.UUID(settled_part))
        with pytest.raises(EarningReversedError):
            await ledger.settle(uuid.UUID(reversed_part))
        # An order that was never paid has no earning to move.
        with pytest.raises(EarningNotRecordedError):
            await ledger.settle(uuid.UUID(part_id(never_paid, "Amina Shop")))
        await session.commit()

    assert await balances(db_client, market.amina) == before == ("0.00", "94499.99", "94499.99")


# ── Revenue, for staff ───────────────────────────────────────────────────


async def test_staff_see_revenue_and_what_muhuze_earned(
    db_client: AsyncClient, admin, market, buy, pay
) -> None:
    await pay(await buy((market.amina, 1), (market.brian, 1)))
    await pay(await buy((market.brian, 1)))

    everything = await db_client.get(f"{API}/revenue/summary", headers=admin.headers)
    brian_only = await db_client.get(
        f"{API}/revenue/summary",
        params={"seller_id": market.brian.seller_id},
        headers=admin.headers,
    )
    records = await db_client.get(
        f"{API}/revenue", params={"seller_id": market.brian.seller_id}, headers=admin.headers
    )
    wallet = await db_client.get(f"{API}/wallets/{market.brian.seller_id}", headers=admin.headers)
    movements = await db_client.get(
        f"{API}/wallets/{market.brian.seller_id}/transactions", headers=admin.headers
    )

    assert everything.json()["data"] == {
        "sales": 3,
        "gross_amount": "1004999.99",
        "commission_amount": "100500.00",  # MUHUZE's income
        "seller_amount": "904499.99",
        "currency": "RWF",
    }
    assert brian_only.json()["data"]["commission_amount"] == "90000.00"
    assert [r["seller_amount"] for r in records.json()["data"]["items"]] == ["405000.00"] * 2
    assert wallet.json()["data"]["pending_balance"] == "810000.00"
    assert movements.json()["data"]["total"] == 2
    # A seller with no wallet yet is shown zeros, not an error.
    empty = await db_client.get(f"{API}/wallets/{uuid.uuid4()}", headers=admin.headers)
    assert empty.json()["data"]["pending_balance"] == "0.00"


# ── Access ───────────────────────────────────────────────────────────────


async def test_a_seller_sees_only_their_own_wallet(
    db_client: AsyncClient, admin, carol, market, buy, pay
) -> None:
    await pay(await buy((market.amina, 1), (market.brian, 1)))

    mine = await db_client.get(MY_WALLET, headers=market.amina.headers)
    assert mine.json()["data"]["seller_id"] == market.amina.seller_id
    assert mine.json()["data"]["pending_balance"] == "94499.99"
    # No way to another seller's wallet, or to revenue, without the staff permissions.
    for path in (
        f"/wallets/{market.brian.seller_id}",
        f"/wallets/{market.brian.seller_id}/transactions",
        "/revenue",
        "/revenue/summary",
    ):
        assert (await db_client.get(API + path, headers=market.amina.headers)).status_code == 403
        assert (await db_client.get(API + path)).status_code == 401
    # A buyer has no wallet.
    assert (await db_client.get(MY_WALLET, headers=carol.headers)).status_code == 403
    assert (await db_client.get(MY_WALLET)).status_code == 401

    # A suspended seller can still see what they are owed.
    await db_client.post(
        f"{API}/sellers/{market.amina.seller_id}/suspend",
        json={"reason": "Under investigation"},
        headers=admin.headers,
    )
    suspended = await db_client.get(MY_WALLET, headers=market.amina.headers)
    assert suspended.status_code == 200
    assert suspended.json()["data"]["pending_balance"] == "94499.99"


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
async def test_no_request_can_change_a_balance(
    db_client: AsyncClient, admin, market, buy, pay, method: str
) -> None:
    await pay(await buy((market.amina, 1)))
    body = {"pending_balance": "0", "available_balance": "99999999", "amount": "99999999"}

    # Invariant 9: there is simply no such endpoint, for the seller or for staff.
    for url, actor in (
        (MY_WALLET, market.amina),
        (f"{MY_WALLET}/transactions", market.amina),
        (f"{API}/wallets/{market.amina.seller_id}", admin),
        (f"{API}/wallets/{market.amina.seller_id}/transactions", admin),
        (f"{API}/revenue", admin),
    ):
        response = await db_client.request(method, url, json=body, headers=actor.headers)
        assert response.status_code == 405

    assert await balances(db_client, market.amina) == ("94499.99", "0.00", "94499.99")
