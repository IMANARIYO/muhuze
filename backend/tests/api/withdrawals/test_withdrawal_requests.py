"""Requesting and managing one's own withdrawals: the amount comes out of the
AVAILABLE balance, never the pending one, and the minimum applies (README
§13.8, §20 W4/W5)."""

import uuid
from decimal import Decimal

from sqlalchemy import select

from app.modules.wallets.wallet_model import Wallet
from app.modules.wallets.wallet_service import WalletService
from tests.api.withdrawals.conftest import API, ask_for, movements, wallet

WITHDRAWALS = f"{API}/withdrawals"


async def test_a_seller_requests_a_withdrawal_and_the_funds_are_reserved(
    db_client, market, add_destination, earnings, session_factory
) -> None:
    destination = await add_destination(market.shop)

    requested = await ask_for(
        db_client, market.shop, amount="100000.00", destination_id=destination["id"]
    )

    assert requested.status_code == 201
    body = requested.json()["data"]
    assert body["status"] == "pending"
    assert body["amount"] == "100000.00"
    assert body["currency"] == "RWF"
    assert body["reason"] is None
    assert body["payout_reference"] is None
    # The destination's details are frozen onto the request (a snapshot).
    assert body["destination_provider"] == destination["provider"]
    assert body["destination_account_number"] == destination["account_number"]

    # 135,000.00 available → the 100,000.00 are reserved, nothing is withdrawn yet.
    assert await wallet(db_client, market.shop) == ("35000.00", "0.00")
    async with session_factory() as session:
        stored = await session.scalar(select(Wallet))
        assert stored.available_balance == Decimal("35000.00")
        assert stored.total_withdrawn == Decimal("0.00")

    ledger = await movements(db_client, market.shop)
    withdrawal_move = ledger[0]  # newest first
    assert withdrawal_move["kind"] == "withdrawal"
    assert withdrawal_move["available_change"] == "-100000.00"
    assert withdrawal_move["available_after"] == "35000.00"
    assert withdrawal_move["withdrawal_id"] == body["id"]
    assert withdrawal_move["order_id"] is None
    assert withdrawal_move["seller_order_id"] is None


async def test_only_available_money_can_be_withdrawn(
    db_client, market, add_destination, earnings
) -> None:
    destination = await add_destination(market.shop)
    await ask_for(db_client, market.shop, amount="100000.00", destination_id=destination["id"])

    # Only 35,000.00 is left available; the 270,000.00 pending are not touchable.
    too_much = await ask_for(
        db_client, market.shop, amount="50000.00", destination_id=destination["id"]
    )
    assert too_much.status_code == 422
    assert await wallet(db_client, market.shop) == ("35000.00", "0.00")


async def test_the_whole_available_balance_can_be_withdrawn_and_no_more(
    db_client, market, add_destination, earnings
) -> None:
    destination = await add_destination(market.shop)
    await ask_for(db_client, market.shop, amount="135000.00", destination_id=destination["id"])

    assert await wallet(db_client, market.shop) == ("0.00", "0.00")

    again = await ask_for(
        db_client, market.shop, amount="1000.00", destination_id=destination["id"]
    )
    assert again.status_code == 422


async def test_the_minimum_amount_is_enforced(db_client, market, add_destination, earnings) -> None:
    destination = await add_destination(market.shop)

    too_small = await ask_for(
        db_client, market.shop, amount="999.99", destination_id=destination["id"]
    )

    assert too_small.status_code == 422
    assert await wallet(db_client, market.shop) == ("135000.00", "0.00")


async def test_requesting_against_a_foreign_or_unknown_destination_is_not_found(
    db_client, market, add_destination, earnings, sign_up, open_shop
) -> None:
    destination = await add_destination(market.shop)
    other = await sign_up("margaret@example.com")
    await open_shop(other, "Margaret Shop")
    other_destination = await add_destination(other, provider="Airtel Money")

    wrong_owner = await ask_for(
        db_client, market.shop, amount="10000.00", destination_id=other_destination["id"]
    )
    assert wrong_owner.status_code == 404

    unknown = await ask_for(
        db_client, market.shop, amount="10000.00", destination_id=str(uuid.uuid4())
    )
    assert unknown.status_code == 404

    own = await ask_for(db_client, market.shop, amount="10000.00", destination_id=destination["id"])
    assert own.status_code == 201  # sanity: Laura's own works


async def test_a_pending_withdrawal_can_be_cancelled_and_the_funds_come_back(
    db_client, market, add_destination, earnings
) -> None:
    destination = await add_destination(market.shop)
    requested = await ask_for(
        db_client, market.shop, amount="100000.00", destination_id=destination["id"]
    )
    withdrawal_id = requested.json()["data"]["id"]

    cancelled = await db_client.post(
        f"{WITHDRAWALS}/mine/{withdrawal_id}/cancel", headers=market.shop.headers
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["data"]["status"] == "cancelled"

    # Repeating a cancel changes nothing: the funds are released once.
    again = await db_client.post(
        f"{WITHDRAWALS}/mine/{withdrawal_id}/cancel", headers=market.shop.headers
    )
    assert again.status_code == 200
    assert await wallet(db_client, market.shop) == ("135000.00", "0.00")
    move = (await movements(db_client, market.shop))[0]
    assert move["kind"] == "withdrawal_release"
    assert move["available_change"] == "100000.00"
    assert move["available_after"] == "135000.00"


async def test_a_seller_lists_and_reads_only_their_own_withdrawals(
    db_client, market, add_destination, earnings
) -> None:
    destination = await add_destination(market.shop)
    first = await ask_for(
        db_client, market.shop, amount="50000.00", destination_id=destination["id"]
    )
    second = await ask_for(
        db_client, market.shop, amount="20000.00", destination_id=destination["id"]
    )

    listed = await db_client.get(f"{WITHDRAWALS}/mine", headers=market.shop.headers)
    assert listed.status_code == 200
    items = listed.json()["data"]["items"]
    assert [item["id"] for item in items] == [
        second.json()["data"]["id"],
        first.json()["data"]["id"],  # newest first
    ]

    single = await db_client.get(
        f"{WITHDRAWALS}/mine/{first.json()['data']['id']}", headers=market.shop.headers
    )
    assert single.status_code == 200
    assert single.json()["data"]["amount"] == "50000.00"

    # A withdrawal that is not theirs does not exist.
    foreign = await db_client.get(f"{WITHDRAWALS}/mine/{uuid.uuid4()}", headers=market.shop.headers)
    assert foreign.status_code == 404
    assert (await db_client.get(f"{WITHDRAWALS}/mine")).status_code == 401


async def test_a_buyer_cannot_touch_withdrawals(db_client, ophelia) -> None:
    assert (await db_client.get(f"{WITHDRAWALS}/mine", headers=ophelia.headers)).status_code == 403
    assert (
        await db_client.post(f"{WITHDRAWALS}", json={}, headers=ophelia.headers)
    ).status_code == 403


async def test_a_suspended_seller_cannot_request_but_can_still_see_history(
    db_client, admin, market, add_destination, earnings
) -> None:
    destination = await add_destination(market.shop)
    requested = await ask_for(
        db_client, market.shop, amount="10000.00", destination_id=destination["id"]
    )
    withdrawal_id = requested.json()["data"]["id"]

    suspended = await db_client.post(
        f"{API}/sellers/{market.shop.seller_id}/suspend",
        json={"reason": "Under review"},
        headers=admin.headers,
    )
    assert suspended.status_code == 200

    # The request gate is the same one as selling: suspended means no.
    blocked = await ask_for(
        db_client, market.shop, amount="1000.00", destination_id=destination["id"]
    )
    assert blocked.status_code == 403
    # But the seller can still see what they asked for (README §15).
    visible = await db_client.get(f"{WITHDRAWALS}/mine", headers=market.shop.headers)
    assert visible.status_code == 200
    assert visible.json()["data"]["total"] == 1
    cancelled = await db_client.post(
        f"{WITHDRAWALS}/mine/{withdrawal_id}/cancel", headers=market.shop.headers
    )
    assert cancelled.status_code == 200


async def test_the_ledger_reconciles_after_withdrawal_movements(
    db_client, market, add_destination, earnings, session_factory
) -> None:
    destination = await add_destination(market.shop)
    requested = await ask_for(
        db_client, market.shop, amount="100000.00", destination_id=destination["id"]
    )
    await db_client.post(
        f"{WITHDRAWALS}/mine/{requested.json()['data']['id']}/cancel",
        headers=market.shop.headers,
    )

    # Invariant 8: the wallet's balances are the sum of its movements.
    async with session_factory() as session:
        assert await WalletService(session).reconcile(uuid.UUID(market.shop.seller_id)) is True
