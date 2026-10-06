"""Seller plans, subscriptions, and commission through the HTTP API, against
a real PostgreSQL database. The commission resolver, which orders will call,
is exercised directly."""

import uuid
from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.clock import utc_now
from app.modules.authorization.authorization_service import AuthorizationService
from app.modules.seller_plans.seller_plan_exceptions import DefaultCommissionRateNotSetError
from app.modules.seller_plans.seller_plan_service import SellerPlanService
from app.modules.sellers.seller_service import SellerService

API = "/api/v1"
PLANS = f"{API}/seller-plans"
SUBSCRIPTIONS = f"{API}/seller-subscriptions"
MINE = f"{SUBSCRIPTIONS}/mine"
DEFAULT_RATE = f"{API}/commission-rates/default"


@pytest.fixture
async def amina(sign_up, open_shop):
    actor = await sign_up("amina@example.com")
    actor.seller_id = await open_shop(actor, "Amina Shop")
    return actor


@pytest.fixture
async def brian(sign_up, open_shop):
    actor = await sign_up("brian@example.com")
    actor.seller_id = await open_shop(actor, "Brian Shop")
    return actor


@pytest.fixture
def create_plan(db_client: AsyncClient, admin):
    async def _create_plan(code: str = "basic", **fields: object) -> dict:
        payload = {
            "code": code,
            "name": code.title(),
            "price": "10000",
            "duration_days": 30,
            "commission_rate": "7",
            **fields,
        }
        response = await db_client.post(PLANS, json=payload, headers=admin.headers)
        assert response.status_code == 201, response.text
        return response.json()["data"]

    return _create_plan


@pytest.fixture
def set_default_rate(db_client: AsyncClient, admin):
    async def _set_default_rate(rate: str = "10", **fields: object) -> dict:
        response = await db_client.post(
            DEFAULT_RATE, json={"rate": rate, **fields}, headers=admin.headers
        )
        assert response.status_code == 201, response.text
        return response.json()["data"]

    return _set_default_rate


@pytest.fixture
def assign(db_client: AsyncClient, admin):
    """An admin gives a plan to a seller directly; it is active at once."""

    async def _assign(seller, plan: dict) -> dict:
        response = await db_client.post(
            SUBSCRIPTIONS,
            json={"seller_id": seller.seller_id, "plan_id": plan["id"]},
            headers=admin.headers,
        )
        assert response.status_code == 201, response.text
        return response.json()["data"]

    return _assign


@pytest.fixture
def resolve(session_factory, file_storage):
    """What an order would get: (rate, source, plan name)."""

    async def _resolve(seller, at: datetime | None = None) -> tuple[str, str, str | None]:
        async with session_factory() as session:
            sellers = SellerService(session, AuthorizationService(session), file_storage)
            terms = await SellerPlanService(session, sellers).resolve_commercial_terms(
                uuid.UUID(seller.seller_id), at
            )
        return (str(terms.commission_rate), terms.source.value, terms.plan_name)

    return _resolve


# ── The default commission rate ──────────────────────────────────────────


async def test_there_is_no_built_in_commission_rate(
    db_client: AsyncClient, admin, amina, resolve
) -> None:
    with pytest.raises(DefaultCommissionRateNotSetError):
        await resolve(amina)

    current = await db_client.get(DEFAULT_RATE, headers=admin.headers)
    mine = await db_client.get(f"{MINE}/terms", headers=amina.headers)

    assert current.status_code == 422
    assert current.json()["message"] == "MUHUZE has not set its commission rate yet"
    # The seller's own page still works; it just has no rate to show.
    assert mine.json()["data"] == {
        "commission_rate": None,
        "source": "not_set",
        "subscription": None,
        "upcoming": [],
        "pending_request": None,
    }


async def test_default_rate_applies_to_sellers_without_a_plan(
    db_client: AsyncClient, admin, amina, set_default_rate, resolve
) -> None:
    rate = await set_default_rate("10", note="Launch rate")

    assert rate["rate"] == "10.00"
    assert rate["is_current"] is True
    assert rate["set_by_account_id"] == admin.id
    assert rate["note"] == "Launch rate"
    assert await resolve(amina) == ("10.00", "default", None)
    mine = (await db_client.get(f"{MINE}/terms", headers=amina.headers)).json()["data"]
    assert (mine["commission_rate"], mine["source"]) == ("10.00", "default")
    current = await db_client.get(DEFAULT_RATE, headers=admin.headers)
    assert current.json()["data"]["id"] == rate["id"]


async def test_a_rate_change_is_a_new_dated_row_and_can_be_scheduled(
    db_client: AsyncClient, admin, amina, set_default_rate, resolve
) -> None:
    await set_default_rate("10")
    next_week = utc_now() + timedelta(days=7)
    scheduled = await set_default_rate("8", effective_from=next_week.isoformat())

    assert scheduled["is_current"] is False
    assert await resolve(amina) == ("10.00", "default", None)  # nothing changes yet
    assert await resolve(amina, next_week + timedelta(days=1)) == ("8.00", "default", None)
    # A sale made before the change is still explained by the rate of its day.
    assert await resolve(amina, next_week - timedelta(days=1)) == ("10.00", "default", None)

    history = await db_client.get(f"{DEFAULT_RATE}/history", headers=admin.headers)
    assert [(r["rate"], r["is_current"]) for r in history.json()["data"]["items"]] == [
        ("8.00", False),
        ("10.00", True),
    ]


@pytest.mark.parametrize(
    "payload",
    [
        {"rate": "-1"},
        {"rate": "100.01"},
        {"rate": "7.555"},  # more than two decimal places
        {"rate": "ten"},
        {},
        {"rate": "5", "effective_from": "2026-10-01T00:00:00"},  # no time zone
    ],
)
async def test_default_rate_validates_its_input(
    db_client: AsyncClient, admin, payload: dict
) -> None:
    response = await db_client.post(DEFAULT_RATE, json=payload, headers=admin.headers)
    assert response.status_code == 422


async def test_a_rate_cannot_be_backdated(db_client: AsyncClient, admin) -> None:
    yesterday = (utc_now() - timedelta(days=1)).isoformat()

    response = await db_client.post(
        DEFAULT_RATE, json={"rate": "5", "effective_from": yesterday}, headers=admin.headers
    )

    assert response.status_code == 422
    assert response.json()["message"] == "The rate can only take effect now or in the future"


# ── Plans ────────────────────────────────────────────────────────────────


async def test_create_plan(db_client: AsyncClient, admin) -> None:
    response = await db_client.post(
        PLANS,
        json={
            "code": "  Business ",
            "name": "Business",
            "description": "For growing shops",
            "price": "30000",
            "duration_days": 30,
            "commission_rate": "4.5",
        },
        headers=admin.headers,
    )

    assert response.status_code == 201
    plan = response.json()["data"]
    assert plan["code"] == "business"  # trimmed and lowercased
    assert plan["price"] == "30000.00"  # decimal strings, never floats
    assert plan["commission_rate"] == "4.50"
    assert (plan["currency"], plan["duration_days"], plan["status"]) == ("RWF", 30, "active")

    duplicate = await db_client.post(
        PLANS,
        json={
            "code": "BUSINESS",
            "name": "X",
            "price": "1",
            "duration_days": 1,
            "commission_rate": "1",
        },
        headers=admin.headers,
    )
    assert duplicate.status_code == 409


async def test_a_free_plan_and_a_zero_commission_plan_are_allowed(create_plan) -> None:
    free = await create_plan("starter", price="0", commission_rate="12")
    partner = await create_plan("partner", price="100000", commission_rate="0")

    assert free["price"] == "0.00"
    assert partner["commission_rate"] == "0.00"


@pytest.mark.parametrize(
    "fields",
    [
        {"code": "Has Space"},
        {"code": "9lives"},
        {"name": ""},
        {"price": "-1"},
        {"price": "10.999"},
        {"duration_days": 0},
        {"duration_days": 5000},
        {"commission_rate": "101"},
        {"commission_rate": "-0.01"},
    ],
)
async def test_create_plan_validates_its_input(db_client: AsyncClient, admin, fields: dict) -> None:
    payload = {
        "code": "basic",
        "name": "Basic",
        "price": "10000",
        "duration_days": 30,
        "commission_rate": "7",
        **fields,
    }
    response = await db_client.post(PLANS, json=payload, headers=admin.headers)
    assert response.status_code == 422


async def test_anyone_can_see_the_plans_on_offer_cheapest_first(
    db_client: AsyncClient, admin, create_plan
) -> None:
    await create_plan("partner", price="100000")
    await create_plan("basic", price="10000")
    retired = await create_plan("legacy", price="5000")
    await db_client.post(f"{PLANS}/{retired['id']}/retire", headers=admin.headers)

    public = await db_client.get(PLANS)  # no token
    staff = await db_client.get(f"{PLANS}/manage", headers=admin.headers)
    only_retired = await db_client.get(
        f"{PLANS}/manage", params={"status": "retired"}, headers=admin.headers
    )

    assert [plan["code"] for plan in public.json()["data"]["items"]] == ["basic", "partner"]
    assert [plan["code"] for plan in staff.json()["data"]["items"]] == [
        "legacy",
        "basic",
        "partner",
    ]
    assert [plan["code"] for plan in only_retired.json()["data"]["items"]] == ["legacy"]


async def test_a_retired_plan_cannot_be_requested_and_can_be_offered_again(
    db_client: AsyncClient, admin, amina, create_plan
) -> None:
    plan = await create_plan()
    await db_client.post(f"{PLANS}/{plan['id']}/retire", headers=admin.headers)

    refused = await db_client.post(MINE, json={"plan_id": plan["id"]}, headers=amina.headers)
    assigned = await db_client.post(
        SUBSCRIPTIONS,
        json={"seller_id": amina.seller_id, "plan_id": plan["id"]},
        headers=admin.headers,
    )
    assert refused.status_code == assigned.status_code == 422
    assert refused.json()["message"] == "This plan is no longer offered"

    await db_client.post(f"{PLANS}/{plan['id']}/reactivate", headers=admin.headers)
    accepted = await db_client.post(MINE, json={"plan_id": plan["id"]}, headers=amina.headers)
    assert accepted.status_code == 201


async def test_a_plan_with_subscriptions_cannot_be_deleted(
    db_client: AsyncClient, admin, amina, create_plan, assign
) -> None:
    used = await create_plan("used")
    unused = await create_plan("unused")
    await assign(amina, used)

    refused = await db_client.delete(f"{PLANS}/{used['id']}", headers=admin.headers)
    deleted = await db_client.delete(f"{PLANS}/{unused['id']}", headers=admin.headers)

    assert refused.status_code == 409
    assert refused.json()["message"] == (
        "Sellers have subscribed to this plan. Retire it instead of deleting it."
    )
    assert deleted.status_code == 200
    assert (
        await db_client.delete(f"{PLANS}/{unused['id']}", headers=admin.headers)
    ).status_code == 404


# ── Requesting and activating ────────────────────────────────────────────


async def test_a_request_waits_until_an_admin_activates_it(
    db_client: AsyncClient, admin, amina, create_plan, set_default_rate, resolve
) -> None:
    await set_default_rate("10")
    plan = await create_plan("basic", price="10000", commission_rate="7")

    requested = await db_client.post(MINE, json={"plan_id": plan["id"]}, headers=amina.headers)

    assert requested.status_code == 201
    request = requested.json()["data"]
    assert (request["status"], request["is_applicable"]) == ("pending", False)
    assert (request["starts_at"], request["ends_at"]) == (None, None)
    assert await resolve(amina) == ("10.00", "default", None)  # a request changes nothing
    waiting = await db_client.get(
        SUBSCRIPTIONS, params={"status": "pending"}, headers=admin.headers
    )
    assert [s["id"] for s in waiting.json()["data"]["items"]] == [request["id"]]

    activated = await db_client.post(
        f"{SUBSCRIPTIONS}/{request['id']}/activate",
        json={"payment_reference": "MOMO-778899"},
        headers=admin.headers,
    )

    assert activated.status_code == 200
    subscription = activated.json()["data"]
    assert (subscription["status"], subscription["is_applicable"]) == ("active", True)
    assert subscription["payment_reference"] == "MOMO-778899"
    starts = datetime.fromisoformat(subscription["starts_at"])
    ends = datetime.fromisoformat(subscription["ends_at"])
    assert ends - starts == timedelta(days=30)
    assert await resolve(amina) == ("7.00", "subscription", "Basic")
    terms = (await db_client.get(f"{MINE}/terms", headers=amina.headers)).json()["data"]
    assert (terms["commission_rate"], terms["source"]) == ("7.00", "subscription")
    assert terms["subscription"]["id"] == subscription["id"]
    assert terms["pending_request"] is None

    again = await db_client.post(
        f"{SUBSCRIPTIONS}/{request['id']}/activate", json={}, headers=admin.headers
    )
    assert again.status_code == 409


async def test_a_subscription_keeps_the_terms_it_was_requested_with(
    db_client: AsyncClient, admin, amina, create_plan, resolve
) -> None:
    plan = await create_plan("basic", price="10000", commission_rate="7")
    request = (
        await db_client.post(MINE, json={"plan_id": plan["id"]}, headers=amina.headers)
    ).json()["data"]

    # The admin makes the plan dearer before, and again after, activating.
    await db_client.patch(
        f"{PLANS}/{plan['id']}",
        json={"price": "15000", "commission_rate": "9"},
        headers=admin.headers,
    )
    activated = await db_client.post(
        f"{SUBSCRIPTIONS}/{request['id']}/activate", json={}, headers=admin.headers
    )
    await db_client.patch(
        f"{PLANS}/{plan['id']}",
        json={"commission_rate": "12", "name": "Basic Plus"},
        headers=admin.headers,
    )

    subscription = activated.json()["data"]
    assert (subscription["price"], subscription["commission_rate"]) == ("10000.00", "7.00")
    assert await resolve(amina) == ("7.00", "subscription", "Basic")


async def test_one_open_request_per_seller_and_it_can_be_withdrawn(
    db_client: AsyncClient, amina, brian, create_plan
) -> None:
    plan = await create_plan()
    request = (
        await db_client.post(MINE, json={"plan_id": plan["id"]}, headers=amina.headers)
    ).json()["data"]
    url = f"{MINE}/{request['id']}/withdraw"

    second = await db_client.post(MINE, json={"plan_id": plan["id"]}, headers=amina.headers)
    by_another_seller = await db_client.post(url, headers=brian.headers)
    withdrawn = await db_client.post(url, headers=amina.headers)
    twice = await db_client.post(url, headers=amina.headers)

    assert second.status_code == 409
    assert second.json()["message"] == "You already have a plan request waiting for a decision"
    assert by_another_seller.status_code == 404  # another seller's request doesn't exist for them
    assert withdrawn.json()["data"]["status"] == "cancelled"
    assert twice.status_code == 409
    # With the request gone, a new one is accepted.
    assert (
        await db_client.post(MINE, json={"plan_id": plan["id"]}, headers=amina.headers)
    ).status_code == 201


async def test_reject_needs_a_reason_the_seller_sees(
    db_client: AsyncClient, admin, amina, create_plan
) -> None:
    plan = await create_plan()
    request = (
        await db_client.post(MINE, json={"plan_id": plan["id"]}, headers=amina.headers)
    ).json()["data"]
    url = f"{SUBSCRIPTIONS}/{request['id']}/reject"

    no_reason = await db_client.post(url, json={}, headers=admin.headers)
    rejected = await db_client.post(
        url, json={"reason": "We did not receive your payment"}, headers=admin.headers
    )

    assert no_reason.status_code == 422
    assert rejected.json()["data"]["status"] == "rejected"
    history = (await db_client.get(MINE, headers=amina.headers)).json()["data"]["items"]
    assert history[0]["status_reason"] == "We did not receive your payment"
    activate = await db_client.post(
        f"{SUBSCRIPTIONS}/{request['id']}/activate", json={}, headers=admin.headers
    )
    assert activate.status_code == 409  # a rejected request cannot be activated afterwards


# ── Renewing, switching, ending ──────────────────────────────────────────


async def test_renewing_the_same_plan_early_adds_on_to_the_current_period(
    db_client: AsyncClient, amina, create_plan, assign, resolve
) -> None:
    plan = await create_plan("basic", commission_rate="7", duration_days=30)
    first = await assign(amina, plan)

    renewal = await assign(amina, plan)

    assert renewal["starts_at"] == first["ends_at"]  # no paid days are lost
    assert (renewal["status"], renewal["is_applicable"]) == ("active", False)
    terms = (await db_client.get(f"{MINE}/terms", headers=amina.headers)).json()["data"]
    assert terms["subscription"]["id"] == first["id"]
    assert [s["id"] for s in terms["upcoming"]] == [renewal["id"]]
    # Covered for 60 days in a row, then back to no plan.
    assert (await resolve(amina, utc_now() + timedelta(days=45)))[1] == "subscription"
    with pytest.raises(DefaultCommissionRateNotSetError):
        await resolve(amina, utc_now() + timedelta(days=61))


async def test_switching_to_a_different_plan_takes_effect_at_once(
    db_client: AsyncClient, amina, create_plan, assign, resolve
) -> None:
    basic = await create_plan("basic", commission_rate="7")
    partner = await create_plan("partner", commission_rate="0")
    first = await assign(amina, basic)
    queued = await assign(amina, basic)  # a renewal waiting to start

    switched = await assign(amina, partner)

    assert (switched["status"], switched["is_applicable"]) == ("active", True)
    assert await resolve(amina) == ("0.00", "subscription", "Partner")
    history = {
        s["id"]: s
        for s in (await db_client.get(MINE, headers=amina.headers)).json()["data"]["items"]
    }
    for replaced in (first, queued):
        assert history[replaced["id"]]["status"] == "cancelled"
        assert history[replaced["id"]]["status_reason"] == "Replaced by a new plan"
        assert history[replaced["id"]]["is_applicable"] is False
    # The one that was running ends at the switch; nothing overlaps the new plan.
    assert history[first["id"]]["ends_at"] <= switched["starts_at"]


async def test_cancelling_puts_the_seller_back_on_the_default_rate(
    db_client: AsyncClient, admin, amina, create_plan, assign, set_default_rate, resolve
) -> None:
    await set_default_rate("10")
    subscription = await assign(amina, await create_plan("basic", commission_rate="7"))
    url = f"{SUBSCRIPTIONS}/{subscription['id']}/cancel"

    no_reason = await db_client.post(url, json={}, headers=admin.headers)
    cancelled = await db_client.post(url, json={"reason": "Payment bounced"}, headers=admin.headers)
    twice = await db_client.post(url, json={"reason": "And again"}, headers=admin.headers)

    assert no_reason.status_code == 422
    data = cancelled.json()["data"]
    assert (data["status"], data["is_applicable"], data["status_reason"]) == (
        "cancelled",
        False,
        "Payment bounced",
    )
    assert twice.status_code == 409
    assert await resolve(amina) == ("10.00", "default", None)


async def test_an_expired_subscription_no_longer_applies(
    amina, create_plan, assign, set_default_rate, resolve
) -> None:
    await set_default_rate("10")
    await assign(amina, await create_plan("basic", commission_rate="7", duration_days=30))

    assert await resolve(amina, utc_now() + timedelta(days=29)) == ("7.00", "subscription", "Basic")
    # No grace period: the default applies from the moment it ends.
    assert await resolve(amina, utc_now() + timedelta(days=31)) == ("10.00", "default", None)


async def test_a_zero_percent_plan_is_a_rate_not_a_missing_one(
    amina, create_plan, assign, set_default_rate, resolve
) -> None:
    await set_default_rate("10")
    await assign(amina, await create_plan("partner", commission_rate="0"))

    assert await resolve(amina) == ("0.00", "subscription", "Partner")


async def test_the_database_refuses_two_active_subscriptions_for_the_same_period(
    amina, create_plan, assign, session_factory
) -> None:
    subscription = await assign(amina, await create_plan())

    # Bypassing the application entirely: the guarantee is in the database.
    async with session_factory() as session:
        with pytest.raises(IntegrityError, match="no_overlap"):
            await session.execute(
                text(
                    "INSERT INTO seller_subscriptions (id, seller_id, plan_id, status, plan_name,"
                    " price, currency, duration_days, commission_rate, starts_at, ends_at)"
                    " SELECT gen_random_uuid(), seller_id, plan_id, 'active', 'Second', 0, 'RWF',"
                    " 30, 0, now() + interval '10 days', now() + interval '40 days'"
                    " FROM seller_subscriptions WHERE id = :id"
                ),
                {"id": subscription["id"]},
            )


# ── Access ───────────────────────────────────────────────────────────────


async def test_assigning_needs_an_active_seller(
    db_client: AsyncClient, admin, user, amina, create_plan
) -> None:
    plan = await create_plan()
    # An application that was never approved has a seller id but is not a seller yet.
    draft = await db_client.post(
        f"{API}/sellers/me",
        json={
            "business_name": "Not Approved Yet",
            "business_phone": "+250788123456",
            "identity_document_type": "passport",
            "identity_document_number": "PC7654321",
            "location": {"province": "Kigali", "district": "Gasabo", "sector": "Remera"},
        },
        headers=user.headers,
    )

    for seller_id in (str(uuid.uuid4()), draft.json()["data"]["id"]):
        response = await db_client.post(
            SUBSCRIPTIONS,
            json={"seller_id": seller_id, "plan_id": plan["id"]},
            headers=admin.headers,
        )
        assert response.status_code == 404
    unknown_plan = await db_client.post(
        SUBSCRIPTIONS,
        json={"seller_id": amina.seller_id, "plan_id": str(uuid.uuid4())},
        headers=admin.headers,
    )
    assert unknown_plan.status_code == 404
    assert unknown_plan.json()["message"] == "Plan not found"


async def test_only_an_active_seller_can_request_a_plan(
    db_client: AsyncClient, admin, user, amina, create_plan
) -> None:
    plan = await create_plan()
    payload = {"plan_id": plan["id"]}

    assert (await db_client.post(MINE, json=payload)).status_code == 401
    assert (await db_client.post(MINE, json=payload, headers=user.headers)).status_code == 403
    assert (await db_client.get(f"{MINE}/terms", headers=user.headers)).status_code == 403

    await db_client.post(
        f"{API}/sellers/{amina.seller_id}/suspend",
        json={"reason": "Under investigation"},
        headers=admin.headers,
    )
    suspended = await db_client.post(MINE, json=payload, headers=amina.headers)
    assert suspended.status_code == 403
    assert suspended.json()["message"] == "Only an approved, active seller can do this"


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/seller-plans/manage"),
        ("POST", "/seller-plans"),
        ("PATCH", "/seller-plans/{id}"),
        ("DELETE", "/seller-plans/{id}"),
        ("POST", "/seller-plans/{id}/retire"),
        ("POST", "/seller-plans/{id}/reactivate"),
        ("GET", "/seller-subscriptions"),
        ("POST", "/seller-subscriptions"),
        ("POST", "/seller-subscriptions/{id}/activate"),
        ("POST", "/seller-subscriptions/{id}/reject"),
        ("POST", "/seller-subscriptions/{id}/cancel"),
        ("GET", "/commission-rates/default"),
        ("GET", "/commission-rates/default/history"),
        ("POST", "/commission-rates/default"),
    ],
)
async def test_staff_endpoints_are_closed_to_sellers(
    db_client: AsyncClient, amina, method: str, path: str
) -> None:
    # A seller holds none of the three staff permissions, even for their own subscription.
    url = API + path.replace("{id}", str(uuid.uuid4()))
    body = {"json": {"rate": "0", "reason": "Because I say so"}} if method != "GET" else {}

    anonymous = await db_client.request(method, url, **body)
    seller = await db_client.request(method, url, headers=amina.headers, **body)

    assert anonymous.status_code == 401
    assert seller.status_code == 403


async def test_a_seller_sees_only_their_own_history(
    db_client: AsyncClient, amina, brian, create_plan, assign
) -> None:
    plan = await create_plan()
    mine = await assign(amina, plan)
    await assign(brian, plan)

    history = await db_client.get(MINE, headers=amina.headers)

    assert [s["id"] for s in history.json()["data"]["items"]] == [mine["id"]]
