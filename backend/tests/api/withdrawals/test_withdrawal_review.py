"""Staff review the queue and pay out by hand (README §20 W6/W8): approve is
an acceptance, complete records what got paid, reject and fail give the money
back. The ledger records every step once (README §14, invariant 12)."""

from tests.api.withdrawals.conftest import API, ask_for, movements, wallet

WITHDRAWALS = f"{API}/withdrawals"


async def test_staff_see_the_whole_queue_and_can_filter_it(
    db_client, admin, market, add_destination, earnings
) -> None:
    destination = await add_destination(market.shop)
    for amount in ("30000.00", "40000.00"):
        await ask_for(db_client, market.shop, amount=amount, destination_id=destination["id"])

    everything = await db_client.get(WITHDRAWALS, headers=admin.headers)
    assert everything.status_code == 200
    assert everything.json()["data"]["total"] == 2

    pending = await db_client.get(WITHDRAWALS, params={"status": "pending"}, headers=admin.headers)
    assert pending.json()["data"]["total"] == 2

    by_seller = await db_client.get(
        WITHDRAWALS, params={"seller_id": market.shop.seller_id}, headers=admin.headers
    )
    by_seller_total = by_seller.json()["data"]["total"]
    assert by_seller_total == 2

    nobody = await db_client.get(WITHDRAWALS, params={"status": "completed"}, headers=admin.headers)
    assert nobody.json()["data"]["items"] == []


async def test_rejecting_a_request_gives_the_money_back(
    db_client, admin, market, add_destination, earnings
) -> None:
    destination = await add_destination(market.shop)
    requested = await ask_for(
        db_client, market.shop, amount="100000.00", destination_id=destination["id"]
    )
    withdrawal_id = requested.json()["data"]["id"]

    rejected = await db_client.post(
        f"{WITHDRAWALS}/{withdrawal_id}/reject",
        json={"reason": "We cannot verify this account yet"},
        headers=admin.headers,
    )

    assert rejected.status_code == 200
    body = rejected.json()["data"]
    assert body["status"] == "rejected"
    assert body["reason"] == "We cannot verify this account yet"
    assert body["reviewed_by_account_id"] == admin.id
    # The reserve is released with a new movement; the amounts stay put.
    assert await wallet(db_client, market.shop) == ("135000.00", "0.00")
    move = (await movements(db_client, market.shop))[0]
    assert move["kind"] == "withdrawal_release"
    assert move["available_change"] == "100000.00"


async def test_approve_then_complete_counts_the_payout_once(
    db_client, admin, market, add_destination, earnings, session_factory
) -> None:
    from sqlalchemy import func, select

    from app.modules.wallets.wallet_model import WalletTransaction

    destination = await add_destination(market.shop)
    requested = await ask_for(
        db_client, market.shop, amount="100000.00", destination_id=destination["id"]
    )
    withdrawal_id = requested.json()["data"]["id"]

    approved = await db_client.post(f"{WITHDRAWALS}/{withdrawal_id}/approve", headers=admin.headers)
    assert approved.status_code == 200
    assert approved.json()["data"]["status"] == "processing"
    # The money stays reserved while staff pay out by hand.
    assert await wallet(db_client, market.shop) == ("35000.00", "0.00")

    # Repeated approvals change nothing.
    assert (
        await db_client.post(f"{WITHDRAWALS}/{withdrawal_id}/approve", headers=admin.headers)
    ).status_code == 200

    completed = await db_client.post(
        f"{WITHDRAWALS}/{withdrawal_id}/complete",
        json={"payout_reference": "MOMO-8821"},
        headers=admin.headers,
    )
    assert completed.status_code == 200
    body = completed.json()["data"]
    assert body["status"] == "completed"
    assert body["payout_reference"] == "MOMO-8821"
    assert body["reviewed_by_account_id"] == admin.id
    # The payout is counted; the reserve was already taken at request time.
    assert await wallet(db_client, market.shop) == ("35000.00", "100000.00")

    # A repeated complete records nothing new.
    again = await db_client.post(
        f"{WITHDRAWALS}/{withdrawal_id}/complete",
        json={"payout_reference": "MOMO-8821"},
        headers=admin.headers,
    )
    assert again.status_code == 200
    assert await wallet(db_client, market.shop) == ("35000.00", "100000.00")
    async with session_factory() as session:
        count = await session.scalar(
            select(func.count())
            .select_from(WalletTransaction)
            .where(
                WalletTransaction.withdrawal_id == withdrawal_id,
                WalletTransaction.kind == "withdrawal_complete",
            )
        )
    assert count == 1

    ledger = await movements(db_client, market.shop)
    kinds = [move["kind"] for move in ledger]
    assert kinds[:3] == ["withdrawal_complete", "withdrawal", "settlement"]
    assert kinds.count("earning") == 3  # one per paid unit
    complete_move = ledger[0]
    assert complete_move["available_change"] == "0.00"
    assert complete_move["withdrawal_id"] == withdrawal_id


async def test_a_failed_payout_gives_the_money_back(
    db_client, admin, market, add_destination, earnings
) -> None:
    destination = await add_destination(market.shop)
    requested = await ask_for(
        db_client, market.shop, amount="100000.00", destination_id=destination["id"]
    )
    withdrawal_id = requested.json()["data"]["id"]
    await db_client.post(f"{WITHDRAWALS}/{withdrawal_id}/approve", headers=admin.headers)

    failed = await db_client.post(
        f"{WITHDRAWALS}/{withdrawal_id}/fail",
        json={"reason": "The mobile money network rejected this transfer"},
        headers=admin.headers,
    )

    assert failed.status_code == 200
    assert failed.json()["data"]["status"] == "failed"
    assert failed.json()["data"]["reason"] == "The mobile money network rejected this transfer"
    assert await wallet(db_client, market.shop) == ("135000.00", "0.00")


async def test_only_the_lifecycle_order_is_allowed(
    db_client, admin, market, add_destination, earnings
) -> None:
    destination = await add_destination(market.shop)
    ids: list[str] = []
    for amount in ("10000.00", "10000.00", "10000.00", "10000.00"):
        requested = await ask_for(
            db_client, market.shop, amount=amount, destination_id=destination["id"]
        )
        ids.append(requested.json()["data"]["id"])

    # A pending request only exists to be approved, rejected, or cancelled.
    for action in ("complete", "fail"):
        response = await db_client.post(
            f"{WITHDRAWALS}/{ids[0]}/{action}",
            json={"reason": "Not possible"},
            headers=admin.headers,
        )
        assert response.status_code == 409

    # Once processing, staff finish it or let it fail; there is no rejection.
    await db_client.post(f"{WITHDRAWALS}/{ids[1]}/approve", headers=admin.headers)
    conflicting = await db_client.post(
        f"{WITHDRAWALS}/{ids[1]}/reject", json={"reason": "Too late"}, headers=admin.headers
    )
    assert conflicting.status_code == 409

    # A rejected request is decided; approving it would revive it.
    await db_client.post(
        f"{WITHDRAWALS}/{ids[2]}/reject",
        json={"reason": "Not enough detail"},
        headers=admin.headers,
    )
    assert (
        await db_client.post(f"{WITHDRAWALS}/{ids[2]}/approve", headers=admin.headers)
    ).status_code == 409

    # A completed one cannot be cancelled by anyone.
    await db_client.post(f"{WITHDRAWALS}/{ids[3]}/approve", headers=admin.headers)
    await db_client.post(
        f"{WITHDRAWALS}/{ids[3]}/complete", json={"payout_reference": None}, headers=admin.headers
    )
    assert (
        await db_client.post(f"{WITHDRAWALS}/mine/{ids[3]}/cancel", headers=market.shop.headers)
    ).status_code == 409


async def test_only_staff_review(db_client, admin, market, add_destination, earnings) -> None:
    destination = await add_destination(market.shop)
    requested = await ask_for(
        db_client, market.shop, amount="10000.00", destination_id=destination["id"]
    )
    withdrawal_id = requested.json()["data"]["id"]

    for url in (WITHDRAWALS, f"{WITHDRAWALS}/{withdrawal_id}"):
        assert (await db_client.get(url, headers=market.shop.headers)).status_code == 403
        assert (await db_client.get(url)).status_code == 401
    for action in ("approve", "reject", "complete", "fail"):
        response = await db_client.post(
            f"{WITHDRAWALS}/{withdrawal_id}/{action}",
            json={"reason": "No"},
            headers=market.shop.headers,
        )
        assert response.status_code == 403


async def test_a_staff_decision_on_an_unknown_withdrawal_is_not_found(db_client, admin) -> None:
    import uuid

    response = await db_client.post(f"{WITHDRAWALS}/{uuid.uuid4()}/approve", headers=admin.headers)
    assert response.status_code == 404
