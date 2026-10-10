"""Payments (manual, Phase 1) through the HTTP API, against a real PostgreSQL
database: MUHUZE's receiving accounts, a buyer submitting a transaction
reference, and staff confirming it, which releases the order to its seller."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from app.modules.authorization.authorization_service import AuthorizationService
from app.modules.categories.category_service import CategoryService
from app.modules.orders.order_model import SellerOrderEvent
from app.modules.orders.order_service import OrderService
from app.modules.payments.payment_model import Payment
from app.modules.payments.payment_service import PaymentService
from app.modules.products.product_service import ProductService
from app.modules.seller_plans.seller_plan_service import SellerPlanService
from app.modules.sellers.seller_service import SellerService
from app.modules.wallets.wallet_service import WalletService

API = "/api/v1"
DESTINATIONS = f"{API}/payment-destinations"
PAYMENTS = f"{API}/payments"
JPEG = b"\xff\xd8\xff\xe0" + b"jpeg-bytes" * 20
DELIVERY = {
    "recipient_name": "Carol Mukamana",
    "recipient_phone": "+250788999000",
    "province": "Kigali",
    "district": "Kicukiro",
    "sector": "Niboye",
}
# Placeholders: real account details are data staff enter, never in the code.
MOMO = {
    "method": "mobile_money",
    "provider": "Example Mobile Money",
    "account_reference": "0780000001",
    "registered_name": "MUHUZE EXAMPLE LTD",
    "instructions": "Dial *000# and choose Pay",
}
BANK = {
    "method": "bank_transfer",
    "provider": "Example Bank",
    "account_reference": "000-111-222",
    "registered_name": "MUHUZE EXAMPLE LTD",
}


def pay_url(order: dict) -> str:
    return f"{API}/orders/mine/{order['id']}/payment"


@pytest.fixture
async def carol(sign_up):
    return await sign_up("carol@example.com")


@pytest.fixture
async def dave(sign_up):
    return await sign_up("dave@example.com")


@pytest.fixture
async def shop(db_client: AsyncClient, admin, sign_up, open_shop):
    """Amina's shop with one product on sale, and a 10% default commission."""
    seller = await sign_up("amina@example.com")
    seller.seller_id = await open_shop(seller, "Amina Shop")
    category = await db_client.post(
        f"{API}/categories", json={"name": "Phones"}, headers=seller.headers
    )
    created = await db_client.post(
        f"{API}/products",
        json={
            "name": "Galaxy S24",
            "price": "850000",
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
    rate = await db_client.post(
        f"{API}/commission-rates/default", json={"rate": "10"}, headers=admin.headers
    )
    assert rate.status_code == 201, rate.text
    return seller


@pytest.fixture
def place(db_client: AsyncClient, shop):
    async def _place(buyer, quantity: int = 1) -> dict:
        response = await db_client.post(
            f"{API}/orders",
            json={
                "items": [{"product_id": shop.product_id, "quantity": quantity}],
                "delivery": DELIVERY,
            },
            headers=buyer.headers,
        )
        assert response.status_code == 201, response.text
        return response.json()["data"]

    return _place


@pytest.fixture
def add_destination(db_client: AsyncClient, admin):
    async def _add_destination(details: dict = MOMO, **overrides: object) -> dict:
        response = await db_client.post(
            DESTINATIONS, json={**details, **overrides}, headers=admin.headers
        )
        assert response.status_code == 201, response.text
        return response.json()["data"]

    return _add_destination


@pytest.fixture
async def momo(add_destination) -> dict:
    return await add_destination(MOMO, is_default=True)


@pytest.fixture
def submit(db_client: AsyncClient):
    async def _submit(buyer, order: dict, destination: dict, reference: str, **fields: object):
        payload = {"destination_id": destination["id"], "reference": reference, **fields}
        if "payer_name" not in payload and "payer_phone" not in payload:
            payload["payer_phone"] = "+250788111222"
        return await db_client.post(pay_url(order), json=payload, headers=buyer.headers)

    return _submit


@pytest.fixture
def submitted(submit):
    """A payment waiting to be verified. Returns the payment."""

    async def _submitted(buyer, order: dict, destination: dict, reference: str = "MP-0001") -> dict:
        response = await submit(buyer, order, destination, reference)
        assert response.status_code == 201, response.text
        return response.json()["data"]

    return _submitted


async def order_status(db_client: AsyncClient, buyer, order: dict) -> tuple[str, list[str]]:
    data = (await db_client.get(f"{API}/orders/mine/{order['id']}", headers=buyer.headers)).json()[
        "data"
    ]
    return data["status"], [part["status"] for part in data["seller_orders"]]


# ── MUHUZE's receiving accounts ──────────────────────────────────────────


async def test_staff_manage_the_accounts_muhuze_is_paid_on(
    db_client: AsyncClient, admin, add_destination
) -> None:
    momo = await add_destination(MOMO, is_default=True)
    bank = await add_destination(BANK)

    assert momo["method"] == "mobile_money"
    assert (momo["currency"], momo["is_active"], momo["is_default"]) == ("RWF", True, True)
    assert bank["is_default"] is False

    updated = await db_client.patch(
        f"{DESTINATIONS}/{bank['id']}",
        json={"account_reference": "999-888-777", "instructions": "Use your order number"},
        headers=admin.headers,
    )
    assert updated.json()["data"]["account_reference"] == "999-888-777"
    assert updated.json()["data"]["provider"] == "Example Bank"  # not sent, unchanged

    listed = await db_client.get(DESTINATIONS, headers=admin.headers)
    assert [d["provider"] for d in listed.json()["data"]["items"]] == [
        "Example Mobile Money",  # the default first
        "Example Bank",
    ]


async def test_there_is_one_default_and_it_is_always_active(
    db_client: AsyncClient, admin, add_destination
) -> None:
    first = await add_destination(MOMO, is_default=True)
    second = await add_destination(BANK, is_default=True)  # takes over as default

    async def flags() -> dict[str, tuple[bool, bool]]:
        listed = await db_client.get(DESTINATIONS, headers=admin.headers)
        return {d["id"]: (d["is_active"], d["is_default"]) for d in listed.json()["data"]["items"]}

    assert await flags() == {first["id"]: (True, False), second["id"]: (True, True)}

    await db_client.post(f"{DESTINATIONS}/{first['id']}/set-default", headers=admin.headers)
    assert await flags() == {first["id"]: (True, True), second["id"]: (True, False)}

    # Deactivating the default leaves no default, rather than a hidden one.
    await db_client.post(f"{DESTINATIONS}/{first['id']}/deactivate", headers=admin.headers)
    assert await flags() == {first["id"]: (False, False), second["id"]: (True, False)}
    refused = await db_client.post(
        f"{DESTINATIONS}/{first['id']}/set-default", headers=admin.headers
    )
    assert refused.status_code == 422
    assert refused.json()["message"] == "Only an active destination can be the default"

    await db_client.post(f"{DESTINATIONS}/{first['id']}/activate", headers=admin.headers)
    assert (await flags())[first["id"]] == (True, False)


@pytest.mark.parametrize(
    "change",
    [
        {"method": "cash"},
        {"provider": ""},
        {"account_reference": "   "},
        {"registered_name": None},
        {"instructions": "x" * 501},
    ],
)
async def test_destination_validates_its_input(db_client: AsyncClient, admin, change: dict) -> None:
    response = await db_client.post(DESTINATIONS, json={**MOMO, **change}, headers=admin.headers)
    assert response.status_code == 422


async def test_a_destination_payments_have_used_cannot_be_deleted(
    db_client: AsyncClient, admin, carol, place, add_destination, submitted
) -> None:
    used = await add_destination(MOMO)
    unused = await add_destination(BANK)
    await submitted(carol, await place(carol), used)

    refused = await db_client.delete(f"{DESTINATIONS}/{used['id']}", headers=admin.headers)
    deleted = await db_client.delete(f"{DESTINATIONS}/{unused['id']}", headers=admin.headers)
    again = await db_client.delete(f"{DESTINATIONS}/{unused['id']}", headers=admin.headers)

    assert refused.status_code == 409
    assert refused.json()["message"] == (
        "Payments have used this destination. Deactivate it instead of deleting it."
    )
    assert deleted.status_code == 200
    assert again.status_code == 404


# ── The buyer: instructions and submitting ───────────────────────────────


async def test_a_buyer_sees_how_to_pay_for_their_own_unpaid_order(
    db_client: AsyncClient, admin, carol, dave, place, add_destination
) -> None:
    order = await place(carol)
    nothing_yet = (await db_client.get(pay_url(order), headers=carol.headers)).json()["data"]
    assert (nothing_yet["can_pay"], nothing_yet["pay_to"]) == (False, [])  # no account set up

    bank = await add_destination(BANK)
    momo = await add_destination(MOMO, is_default=True)
    hidden = await add_destination(MOMO, provider="Retired account")
    await db_client.post(f"{DESTINATIONS}/{hidden['id']}/deactivate", headers=admin.headers)

    response = await db_client.get(pay_url(order), headers=carol.headers)

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["order_id"] == order["id"]
    assert data["order_number"] == order["order_number"]
    assert (data["amount"], data["currency"]) == ("850000.00", "RWF")
    assert data["can_pay"] is True
    assert data["attempts"] == []
    # Only active accounts, the default first, and only what a buyer needs.
    assert [p["id"] for p in data["pay_to"]] == [momo["id"], bank["id"]]
    assert data["pay_to"][0] == {
        "id": momo["id"],
        "method": "mobile_money",
        "provider": "Example Mobile Money",
        "account_reference": "0780000001",
        "registered_name": "MUHUZE EXAMPLE LTD",
        "instructions": "Dial *000# and choose Pay",
        "is_default": True,
    }
    # Another buyer's order is not found: no listing of MUHUZE's accounts for outsiders.
    assert (await db_client.get(pay_url(order), headers=dave.headers)).status_code == 404
    assert (await db_client.get(pay_url(order))).status_code == 401


async def test_submitting_a_reference_does_not_pay_the_order(
    db_client: AsyncClient, shop, carol, place, momo, submit
) -> None:
    order = await place(carol)

    response = await submit(
        carol, order, momo, "  MP240001.ABCD  ", payer_phone="+250788111222", payer_name="Carol M"
    )

    assert response.status_code == 201
    payment = response.json()["data"]
    assert payment["status"] == "awaiting_verification"
    assert (payment["amount"], payment["currency"]) == ("850000.00", "RWF")
    assert payment["reference"] == "MP240001.ABCD"
    assert payment["destination_account_reference"] == "0780000001"
    assert payment["paid_at"] is None
    # Nothing is paid until staff check the statement (README §12.7).
    assert await order_status(db_client, carol, order) == ("awaiting_payment", ["awaiting_payment"])
    seller_view = await db_client.get(f"{API}/seller-orders/mine", headers=shop.headers)
    assert seller_view.json()["data"]["total"] == 0

    instructions = (await db_client.get(pay_url(order), headers=carol.headers)).json()["data"]
    assert instructions["can_pay"] is False  # one attempt at a time
    assert [a["id"] for a in instructions["attempts"]] == [payment["id"]]


async def test_a_payment_is_always_for_the_whole_order(
    db_client: AsyncClient, carol, place, momo
) -> None:
    order = await place(carol, quantity=3)

    response = await db_client.post(
        pay_url(order),
        json={
            "destination_id": momo["id"],
            "reference": "MP-PART",
            "payer_name": "Carol",
            "amount": "1",  # a client cannot choose what it pays
            "status": "paid",
        },
        headers=carol.headers,
    )

    assert response.status_code == 201
    assert response.json()["data"]["amount"] == "2550000.00"
    assert response.json()["data"]["status"] == "awaiting_verification"


@pytest.mark.parametrize(
    "change",
    [
        {"reference": "ab"},
        {"reference": "x" * 101},
        {"destination_id": "not-a-uuid"},
        {"payer_phone": "0788111222"},
        {"payer_phone": None, "payer_name": None},  # nobody to match it to
    ],
)
async def test_submit_validates_its_input(
    db_client: AsyncClient, carol, place, momo, change: dict
) -> None:
    payload = {
        "destination_id": momo["id"],
        "reference": "MP-0001",
        "payer_phone": "+250788111222",
        **change,
    }
    response = await db_client.post(
        pay_url(await place(carol)), json=payload, headers=carol.headers
    )
    assert response.status_code == 422


async def test_only_an_active_destination_can_be_paid_to(
    db_client: AsyncClient, admin, carol, place, add_destination, submit
) -> None:
    inactive = await add_destination(BANK)
    await db_client.post(f"{DESTINATIONS}/{inactive['id']}/deactivate", headers=admin.headers)
    order = await place(carol)

    to_inactive = await submit(carol, order, inactive, "MP-0001")
    to_unknown = await submit(carol, order, {"id": str(uuid.uuid4())}, "MP-0002")

    assert to_inactive.status_code == to_unknown.status_code == 422
    assert to_inactive.json()["message"] == (
        "This payment destination is not available. Choose one of the listed accounts."
    )


async def test_one_attempt_at_a_time_and_only_for_your_own_unpaid_order(
    db_client: AsyncClient, carol, dave, place, momo, submit, submitted
) -> None:
    order = await place(carol)
    await submitted(carol, order, momo)
    cancelled = await place(carol)
    await db_client.post(
        f"{API}/orders/mine/{cancelled['id']}/cancel", json={}, headers=carol.headers
    )

    second = await submit(carol, order, momo, "MP-0002")
    someone_elses = await submit(dave, order, momo, "MP-0003")
    for_cancelled = await submit(carol, cancelled, momo, "MP-0004")

    assert second.status_code == 409
    assert second.json()["message"] == "A payment for this order is already waiting to be verified"
    assert someone_elses.status_code == 404
    assert for_cancelled.status_code == 409
    assert for_cancelled.json()["message"] == "This order is not waiting for payment"


async def test_a_transaction_reference_can_be_used_only_once(
    db_client: AsyncClient, admin, carol, dave, place, momo, submit, submitted, session_factory
) -> None:
    first = await submitted(carol, await place(carol), momo, "MP240001.ABCD")
    other_order = await place(dave)

    reused = await submit(dave, other_order, momo, "mp240001.abcd")  # letter case doesn't matter

    assert reused.status_code == 409
    assert reused.json()["message"] == "This transaction reference has already been used"
    # Still refused once the first payment is paid.
    await db_client.post(f"{PAYMENTS}/{first['id']}/approve", headers=admin.headers)
    assert (await submit(dave, other_order, momo, "MP240001.ABCD")).status_code == 409
    # And the database refuses it even if the application is bypassed.
    async with session_factory() as session:
        with pytest.raises(IntegrityError, match="uq_payments_reference_lower"):
            await session.execute(
                text(
                    "INSERT INTO payments (id, order_id, order_number, payer_account_id, amount,"
                    " currency, destination_id, destination_method, destination_provider,"
                    " destination_account_reference, destination_registered_name, reference)"
                    " SELECT gen_random_uuid(), :order_id, 'X', payer_account_id, amount, currency,"
                    " destination_id, destination_method, destination_provider,"
                    " destination_account_reference, destination_registered_name, 'MP240001.abcd'"
                    " FROM payments WHERE id = :id"
                ),
                {"id": first["id"], "order_id": other_order["id"]},
            )


# ── Staff: approving ─────────────────────────────────────────────────────


async def test_approving_marks_it_paid_and_releases_the_order_to_the_seller(
    db_client: AsyncClient, admin, shop, carol, place, momo, submitted
) -> None:
    order = await place(carol)
    payment = await submitted(carol, order, momo, "MP-0001")

    response = await db_client.post(f"{PAYMENTS}/{payment['id']}/approve", headers=admin.headers)

    assert response.status_code == 200
    approved = response.json()["data"]
    assert approved["status"] == "paid"
    assert approved["paid_at"] is not None
    assert approved["verified_by_account_id"] == admin.id  # who approved is recorded
    assert approved["verified_at"] is not None
    # The order is paid and its part is now the seller's to handle.
    assert await order_status(db_client, carol, order) == ("in_progress", ["pending"])
    seller_orders = await db_client.get(f"{API}/seller-orders/mine", headers=shop.headers)
    (released,) = seller_orders.json()["data"]["items"]
    assert (released["order_number"], released["seller_amount"]) == (
        order["order_number"],
        "765000.00",  # 850000 less the 10% commission
    )
    instructions = (await db_client.get(pay_url(order), headers=carol.headers)).json()["data"]
    assert (instructions["can_pay"], instructions["pay_to"]) == (False, [])
    assert [a["status"] for a in instructions["attempts"]] == ["paid"]


async def test_approving_twice_changes_nothing(
    db_client: AsyncClient, admin, shop, carol, place, momo, submitted, session_factory
) -> None:
    order = await place(carol)
    payment = await submitted(carol, order, momo)
    url = f"{PAYMENTS}/{payment['id']}/approve"

    first = await db_client.post(url, headers=admin.headers)
    second = await db_client.post(url, headers=admin.headers)  # a double click, or a retry

    assert first.status_code == second.status_code == 200
    assert second.json()["data"]["paid_at"] == first.json()["data"]["paid_at"]
    # Persisted effects happened exactly once (README §12.8).
    async with session_factory() as session:
        paid = list(
            await session.scalars(
                select(Payment).where(
                    Payment.order_id == uuid.UUID(order["id"]), Payment.status == "paid"
                )
            )
        )
        released = list(
            await session.scalars(
                select(SellerOrderEvent).where(SellerOrderEvent.to_status == "pending")
            )
        )
    assert len(paid) == 1
    assert len(released) == 1
    assert await order_status(db_client, carol, order) == ("in_progress", ["pending"])


async def test_a_gateway_would_confirm_through_the_same_function(
    db_client: AsyncClient, shop, carol, place, momo, submitted, session_factory, file_storage
) -> None:
    order = await place(carol)
    payment = await submitted(carol, order, momo)

    # No member of staff: `verified_by=None` is how an automated confirmation calls it.
    async with session_factory() as session:
        sellers = SellerService(session, AuthorizationService(session), file_storage)
        products = ProductService(session, CategoryService(session), sellers, file_storage)
        orders = OrderService(
            session,
            products,
            SellerPlanService(session, sellers),
            sellers,
            WalletService(session),
        )
        service = PaymentService(session, orders)
        confirmed = await service.confirm_payment(uuid.UUID(payment["id"]), verified_by=None)
        again = await service.confirm_payment(uuid.UUID(payment["id"]), verified_by=None)

    assert confirmed.status == again.status == "paid"
    assert confirmed.verified_by_account_id is None
    # Everything downstream is identical to a manual approval.
    assert await order_status(db_client, carol, order) == ("in_progress", ["pending"])


async def test_rejecting_lets_the_buyer_try_again_and_keeps_the_record(
    db_client: AsyncClient, admin, carol, place, momo, submit, submitted
) -> None:
    order = await place(carol)
    wrong = await submitted(carol, order, momo, "MP-WRONG")
    url = f"{PAYMENTS}/{wrong['id']}/reject"

    no_reason = await db_client.post(url, json={}, headers=admin.headers)
    rejected = await db_client.post(
        url, json={"reason": "No such transfer on our statement"}, headers=admin.headers
    )
    twice = await db_client.post(url, json={"reason": "Still not there"}, headers=admin.headers)

    assert no_reason.status_code == 422
    assert rejected.json()["data"]["status"] == "rejected"
    assert rejected.json()["data"]["verified_by_account_id"] == admin.id
    assert twice.status_code == 409
    assert await order_status(db_client, carol, order) == ("awaiting_payment", ["awaiting_payment"])
    instructions = (await db_client.get(pay_url(order), headers=carol.headers)).json()["data"]
    assert instructions["can_pay"] is True
    assert instructions["attempts"][0]["rejection_reason"] == "No such transfer on our statement"

    retry = await submit(carol, order, momo, "MP-RIGHT")
    assert retry.status_code == 201
    approved = await db_client.post(
        f"{PAYMENTS}/{retry.json()['data']['id']}/approve", headers=admin.headers
    )
    assert approved.json()["data"]["status"] == "paid"
    instructions = (await db_client.get(pay_url(order), headers=carol.headers)).json()["data"]
    assert [a["status"] for a in instructions["attempts"]] == ["paid", "rejected"]
    # A rejected attempt cannot be revived.
    revive = await db_client.post(f"{PAYMENTS}/{wrong['id']}/approve", headers=admin.headers)
    assert revive.status_code == 409


async def test_a_rejected_reference_can_be_submitted_again(
    db_client: AsyncClient, admin, carol, place, momo, submit, submitted
) -> None:
    order = await place(carol)
    first = await submitted(carol, order, momo, "MP-0001")
    await db_client.post(
        f"{PAYMENTS}/{first['id']}/reject",
        json={"reason": "Not on the statement yet, try later"},
        headers=admin.headers,
    )

    # The transfer shows up later: the same reference is valid after all.
    assert (await submit(carol, order, momo, "MP-0001")).status_code == 201


async def test_a_payment_keeps_the_account_it_was_made_to(
    db_client: AsyncClient, admin, carol, place, momo, submitted
) -> None:
    payment = await submitted(carol, await place(carol), momo)

    # MUHUZE changes its number, then retires the account.
    await db_client.patch(
        f"{DESTINATIONS}/{momo['id']}",
        json={"account_reference": "0789999999", "registered_name": "MUHUZE NEW NAME"},
        headers=admin.headers,
    )
    await db_client.post(f"{DESTINATIONS}/{momo['id']}/deactivate", headers=admin.headers)

    stored = (await db_client.get(f"{PAYMENTS}/{payment['id']}", headers=admin.headers)).json()
    assert stored["data"]["destination_account_reference"] == "0780000001"
    assert stored["data"]["destination_registered_name"] == "MUHUZE EXAMPLE LTD"
    # It can still be approved: the money was sent to a real MUHUZE account at the time.
    approved = await db_client.post(f"{PAYMENTS}/{payment['id']}/approve", headers=admin.headers)
    assert approved.json()["data"]["status"] == "paid"


async def test_an_order_cancelled_meanwhile_is_not_paid(
    db_client: AsyncClient, admin, carol, place, momo, submitted
) -> None:
    order = await place(carol)
    payment = await submitted(carol, order, momo)
    await db_client.post(f"{API}/orders/mine/{order['id']}/cancel", json={}, headers=carol.headers)

    response = await db_client.post(f"{PAYMENTS}/{payment['id']}/approve", headers=admin.headers)

    assert response.status_code == 409
    assert response.json()["message"] == "A cancelled order cannot be paid"
    # Nothing was half-done: the payment is still waiting, for staff to reject.
    stored = (await db_client.get(f"{PAYMENTS}/{payment['id']}", headers=admin.headers)).json()
    assert stored["data"]["status"] == "awaiting_verification"
    assert (await order_status(db_client, carol, order))[0] == "cancelled"


async def test_staff_cannot_verify_a_payment_they_made_themselves(
    db_client: AsyncClient, admin, place, momo, submitted
) -> None:
    payment = await submitted(admin, await place(admin), momo)

    approved = await db_client.post(f"{PAYMENTS}/{payment['id']}/approve", headers=admin.headers)
    rejected = await db_client.post(
        f"{PAYMENTS}/{payment['id']}/reject",
        json={"reason": "Testing myself"},
        headers=admin.headers,
    )

    assert approved.status_code == rejected.status_code == 422
    assert approved.json()["message"] == "You cannot verify a payment you made yourself"


async def test_staff_queue_is_oldest_first_and_searchable(
    db_client: AsyncClient, admin, carol, dave, place, momo, submitted
) -> None:
    carols_order = await place(carol)
    first = await submitted(carol, carols_order, momo, "MP-AAA-111")
    second = await submitted(dave, await place(dave), momo, "BANK-BBB-222")
    await db_client.post(f"{PAYMENTS}/{first['id']}/approve", headers=admin.headers)

    async def ids(**params: object) -> list[str]:
        response = await db_client.get(PAYMENTS, params=params, headers=admin.headers)
        assert response.status_code == 200, response.text
        return [payment["id"] for payment in response.json()["data"]["items"]]

    assert await ids() == [first["id"], second["id"]]  # the longest-waiting first
    assert await ids(status="awaiting_verification") == [second["id"]]
    assert await ids(status="paid") == [first["id"]]
    assert await ids(q="bank-bbb") == [second["id"]]  # by reference, any letter case
    assert await ids(q=carols_order["order_number"]) == [first["id"]]  # or by order number

    detail = (await db_client.get(f"{PAYMENTS}/{second['id']}", headers=admin.headers)).json()
    assert detail["data"]["payer_account_id"] == dave.id
    assert detail["data"]["payer_phone"] == "+250788111222"
    assert detail["data"]["channel"] == "manual"
    missing = await db_client.get(f"{PAYMENTS}/{uuid.uuid4()}", headers=admin.headers)
    assert missing.status_code == 404


# ── Access ───────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/payments"),
        ("GET", "/payments/{id}"),
        ("POST", "/payments/{id}/approve"),
        ("POST", "/payments/{id}/reject"),
        ("GET", "/payment-destinations"),
        ("POST", "/payment-destinations"),
        ("PATCH", "/payment-destinations/{id}"),
        ("DELETE", "/payment-destinations/{id}"),
        ("POST", "/payment-destinations/{id}/activate"),
        ("POST", "/payment-destinations/{id}/deactivate"),
        ("POST", "/payment-destinations/{id}/set-default"),
    ],
)
async def test_staff_endpoints_are_closed_to_buyers_and_sellers(
    db_client: AsyncClient, shop, carol, method: str, path: str
) -> None:
    url = API + path.replace("{id}", str(uuid.uuid4()))
    body = {"json": {**MOMO, "reason": "Because I say so"}} if method in ("POST", "PATCH") else {}

    assert (await db_client.request(method, url, **body)).status_code == 401
    for actor in (carol, shop):
        response = await db_client.request(method, url, headers=actor.headers, **body)
        assert response.status_code == 403
