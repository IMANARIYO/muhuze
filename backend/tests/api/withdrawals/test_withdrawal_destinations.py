"""The seller's payout destinations: own them, keep them current, and never
let a used account be deleted (README §13.8, §20 W8)."""

import uuid

from tests.api.withdrawals.conftest import API, ask_for

DESTINATIONS = f"{API}/withdrawal/destinations"


async def test_a_seller_adds_and_sees_their_payout_destinations(
    db_client, shop, add_destination
) -> None:
    mobile = await add_destination(shop)
    bank = await add_destination(
        shop,
        type="bank",
        provider="Bank of Kigali",
        account_number="000123456789",
        account_name="LAURA WAREHOUSE",
    )

    response = await db_client.get(f"{DESTINATIONS}/mine", headers=shop.headers)

    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert {item["id"] for item in items} == {mobile["id"], bank["id"]}
    assert all(item["is_active"] for item in items)
    bank_row = next(item for item in items if item["id"] == bank["id"])
    assert bank_row["type"] == "bank"
    assert bank_row["account_number"] == "000123456789"


async def test_a_destination_is_updated_only_with_the_fields_sent(
    db_client, shop, add_destination
) -> None:
    destination = await add_destination(shop)

    updated = await db_client.patch(
        f"{DESTINATIONS}/{destination['id']}",
        json={"provider": "Airtel Money"},
        headers=shop.headers,
    )
    assert updated.status_code == 200
    body = updated.json()["data"]
    assert body["provider"] == "Airtel Money"
    assert body["account_number"] == destination["account_number"]

    # Null is not an allowed update; the account must stay intact.
    bad = await db_client.patch(
        f"{DESTINATIONS}/{destination['id']}",
        json={"account_number": None},
        headers=shop.headers,
    )
    assert bad.status_code == 422


async def test_deactivating_a_destination_stops_new_use_but_keeps_history(
    db_client, market, add_destination, earnings
) -> None:
    destination = await add_destination(market.shop)
    await db_client.post(
        f"{DESTINATIONS}/{destination['id']}/deactivate", headers=market.shop.headers
    )

    asked = await ask_for(
        db_client, market.shop, amount="10000.00", destination_id=destination["id"]
    )
    assert asked.status_code == 422  # deactivated: choose an active one

    activated = await db_client.post(
        f"{DESTINATIONS}/{destination['id']}/activate", headers=market.shop.headers
    )
    assert activated.status_code == 200
    asked = await ask_for(
        db_client, market.shop, amount="10000.00", destination_id=destination["id"]
    )
    assert asked.status_code == 201


async def test_a_used_destination_is_deactivated_never_deleted(
    db_client, market, add_destination, earnings
) -> None:
    destination = await add_destination(market.shop)
    created = await ask_for(
        db_client, market.shop, amount="10000.00", destination_id=destination["id"]
    )
    assert created.status_code == 201

    deleted = await db_client.delete(
        f"{DESTINATIONS}/{destination['id']}", headers=market.shop.headers
    )
    assert deleted.status_code == 409  # a withdrawal has used it

    deactivated = await db_client.post(
        f"{DESTINATIONS}/{destination['id']}/deactivate", headers=market.shop.headers
    )
    assert deactivated.status_code == 200
    still_there = await db_client.get(f"{DESTINATIONS}/mine", headers=market.shop.headers)
    assert any(d["id"] == destination["id"] for d in still_there.json()["data"]["items"])


async def test_destinations_are_owned_and_not_shared(
    db_client, shop, add_destination, ophelia
) -> None:
    destination = await add_destination(shop)

    # Nobody else can read, change, or remove it.
    for method, url, body in (
        ("GET", f"{DESTINATIONS}/mine", None),
        ("PATCH", f"{DESTINATIONS}/{destination['id']}", {"provider": "Changed"}),
        ("DELETE", f"{DESTINATIONS}/{destination['id']}", None),
    ):
        assert (
            await db_client.request(method, url, json=body, headers=ophelia.headers)
        ).status_code == 403
        assert (await db_client.request(method, url, json=body)).status_code == 401

    # Another seller's destination does not exist from here.
    made_up = await db_client.post(
        f"{DESTINATIONS}/{uuid.uuid4()}/deactivate", headers=shop.headers
    )
    assert made_up.status_code == 404
