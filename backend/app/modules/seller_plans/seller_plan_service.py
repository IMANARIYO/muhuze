"""Seller plans, subscriptions, and the commission a seller is charged.
Rules are documented in docs/features/017_seller_plans.md and README §10.

`resolve_commercial_terms` is the ONLY place a commission rate is decided:

    a subscription in force  → its commission rate (may be 0%)
    none                     → the current default commission rate

Orders will call it once, when a SellerOrder is created, and store the
answer. Nothing here ever changes a past sale.

No plan name, price, or rate is written in code: they are data admins enter.
Every public method except the resolver is one unit of work and commits it.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import utc_now
from app.core.logging import get_logger
from app.modules.seller_plans.seller_plan_constants import (
    REPLACED_REASON,
    PlanStatus,
    SubscriptionStatus,
    TermsSource,
)
from app.modules.seller_plans.seller_plan_exceptions import (
    DefaultCommissionRateNotSetError,
    EffectiveDateInPastError,
    EffectiveDateTakenError,
    PendingSubscriptionExistsError,
    SellerPlanCodeTakenError,
    SellerPlanInUseError,
    SellerPlanNotFoundError,
    SellerPlanRetiredError,
    SellerSubscriptionNotFoundError,
    SubscriptionPeriodConflictError,
    SubscriptionStatusConflictError,
)
from app.modules.seller_plans.seller_plan_model import (
    DefaultCommissionRate,
    SellerPlan,
    SellerSubscription,
)
from app.modules.seller_plans.seller_plan_repository import SellerPlanRepository
from app.modules.seller_plans.seller_plan_schema import (
    CommercialTermsResponse,
    DefaultCommissionRateRequest,
    DefaultCommissionRateResponse,
    SellerPlanCreateRequest,
    SellerPlanResponse,
    SellerPlanUpdateRequest,
    SellerSubscriptionResponse,
    StaffPlanFilters,
    StaffSubscriptionFilters,
    SubscriptionAssignRequest,
)
from app.modules.sellers.seller_service import SellerService
from app.shared.responses.pagination import Page, PaginationParams

logger = get_logger(__name__)

PENDING_INDEX = "uq_seller_subscriptions_seller_id_pending"
# A few seconds of tolerance, so "now" sent by a client isn't rejected as past.
EFFECTIVE_FROM_TOLERANCE = timedelta(seconds=60)


@dataclass(frozen=True, slots=True)
class CommercialTerms:
    """What applies to a seller at one moment. An order copies this."""

    commission_rate: Decimal
    source: TermsSource
    # Set when the rate comes from a subscription.
    subscription_id: uuid.UUID | None = None
    plan_id: uuid.UUID | None = None
    plan_name: str | None = None
    # Set when the rate is the default.
    default_rate_id: uuid.UUID | None = None


class SellerPlanService:
    def __init__(self, session: AsyncSession, seller_service: SellerService) -> None:
        self._session = session
        self._sellers = seller_service
        self._repository = SellerPlanRepository(session)

    # ── Used by other features ───────────────────────────────────────────

    async def resolve_commercial_terms(
        self, seller_id: uuid.UUID, at: datetime | None = None
    ) -> CommercialTerms:
        """The commission terms for a seller at `at` (default: now). Read
        only: it commits nothing, so it can run inside another feature's
        transaction. Raises if there is neither a subscription in force nor
        a default rate."""
        at = at or utc_now()
        subscription = await self._repository.get_applicable(seller_id, at)
        if subscription is not None:
            return CommercialTerms(
                commission_rate=subscription.commission_rate,
                source=TermsSource.SUBSCRIPTION,
                subscription_id=subscription.id,
                plan_id=subscription.plan_id,
                plan_name=subscription.plan_name,
            )
        default = await self._repository.get_default_rate(at)
        if default is None:
            raise DefaultCommissionRateNotSetError()
        return CommercialTerms(
            commission_rate=default.rate, source=TermsSource.DEFAULT, default_rate_id=default.id
        )

    # ── Plans ────────────────────────────────────────────────────────────

    async def list_offered_plans(self, pagination: PaginationParams) -> Page[SellerPlanResponse]:
        """The plans a seller can request today."""
        return await self._plan_page(pagination, status=PlanStatus.ACTIVE.value)

    async def list_all_plans(
        self, pagination: PaginationParams, filters: StaffPlanFilters
    ) -> Page[SellerPlanResponse]:
        return await self._plan_page(
            pagination, status=filters.status.value if filters.status else None
        )

    async def get_plan(self, plan_id: uuid.UUID) -> SellerPlan:
        plan = await self._repository.get_plan(plan_id)
        if plan is None:
            raise SellerPlanNotFoundError()
        return plan

    async def create_plan(
        self, *, payload: SellerPlanCreateRequest, created_by: uuid.UUID
    ) -> SellerPlan:
        if await self._repository.get_plan_by_code(payload.code) is not None:
            raise SellerPlanCodeTakenError()
        plan = SellerPlan(
            code=payload.code,
            name=payload.name,
            description=payload.description or None,
            price=_two_places(payload.price),
            duration_days=payload.duration_days,
            commission_rate=_two_places(payload.commission_rate),
            created_by_account_id=created_by,
        )
        try:
            await self._repository.add_plan(plan)
        except IntegrityError as exc:
            await self._session.rollback()
            raise SellerPlanCodeTakenError() from exc
        await self._session.commit()
        logger.info(
            "seller plan created", extra={"plan": plan.code, "by_account_id": str(created_by)}
        )
        return plan

    async def update_plan(
        self, plan_id: uuid.UUID, *, payload: SellerPlanUpdateRequest, updated_by: uuid.UUID
    ) -> SellerPlan:
        """Change what the plan offers from now on. Subscriptions already
        requested keep the terms they recorded."""
        plan = await self.get_plan(plan_id)
        changes = payload.model_dump(exclude_unset=True)
        if "description" in changes:
            changes["description"] = changes["description"] or None
        for field in ("price", "commission_rate"):
            if field in changes:
                changes[field] = _two_places(changes[field])
        for field, value in changes.items():
            setattr(plan, field, value)
        await self._session.commit()
        logger.info(
            "seller plan updated",
            extra={
                "plan": plan.code,
                "fields": sorted(changes),
                "by_account_id": str(updated_by),
            },
        )
        return plan

    async def set_plan_status(
        self, plan_id: uuid.UUID, status: PlanStatus, *, changed_by: uuid.UUID
    ) -> SellerPlan:
        """Retire a plan (no new requests) or offer it again."""
        plan = await self.get_plan(plan_id)
        plan.status = status.value
        await self._session.commit()
        logger.info(
            "seller plan status changed",
            extra={"plan": plan.code, "status": status.value, "by_account_id": str(changed_by)},
        )
        return plan

    async def delete_plan(self, plan_id: uuid.UUID, *, deleted_by: uuid.UUID) -> None:
        """Delete a plan nobody ever subscribed to. Otherwise retire it."""
        plan = await self.get_plan(plan_id)
        code = plan.code
        try:
            await self._repository.delete_plan(plan)
        except IntegrityError as exc:
            await self._session.rollback()
            raise SellerPlanInUseError() from exc
        await self._session.commit()
        logger.info("seller plan deleted", extra={"plan": code, "by_account_id": str(deleted_by)})

    # ── A seller's own subscriptions ─────────────────────────────────────

    async def get_own_terms(self, seller_id: uuid.UUID) -> CommercialTermsResponse:
        """What the seller is charged right now, what is scheduled next, and
        any request still waiting."""
        now = utc_now()
        unfinished = await self._repository.list_unfinished_active(seller_id, now)
        current = next((s for s in unfinished if s.starts_at <= now), None)
        pending = await self._repository.get_pending(seller_id)

        if current is not None:
            rate, source = current.commission_rate, TermsSource.SUBSCRIPTION
        else:
            default = await self._repository.get_default_rate(now)
            rate = default.rate if default else None
            source = TermsSource.DEFAULT if default else TermsSource.NOT_SET
        return CommercialTermsResponse(
            commission_rate=rate,
            source=source,
            subscription=_subscription_response(current, now) if current else None,
            upcoming=[_subscription_response(s, now) for s in unfinished if s.starts_at > now],
            pending_request=_subscription_response(pending, now) if pending else None,
        )

    async def list_own_subscriptions(
        self, *, seller_id: uuid.UUID, pagination: PaginationParams
    ) -> Page[SellerSubscriptionResponse]:
        subscriptions, total = await self._repository.list_subscriptions(
            pagination, seller_id=seller_id
        )
        return _subscription_page(subscriptions, total, pagination)

    async def request_plan(
        self, *, seller_id: uuid.UUID, plan_id: uuid.UUID, requested_by: uuid.UUID
    ) -> SellerSubscriptionResponse:
        """Ask for a plan. It waits as `pending` until an admin, having
        checked the payment, activates it. One open request at a time."""
        plan = await self._offered_plan(plan_id)
        if await self._repository.get_pending(seller_id) is not None:
            raise PendingSubscriptionExistsError()
        subscription = _new_subscription(seller_id, plan, requested_by)
        try:
            await self._repository.add_subscription(subscription)
        except IntegrityError as exc:
            # Lost a race with another request from the same seller.
            await self._session.rollback()
            raise PendingSubscriptionExistsError() from exc
        await self._session.commit()
        logger.info(
            "plan requested", extra={"subscription_id": str(subscription.id), "plan": plan.code}
        )
        return _subscription_response(subscription, utc_now())

    async def withdraw_request(
        self, *, seller_id: uuid.UUID, subscription_id: uuid.UUID, withdrawn_by: uuid.UUID
    ) -> SellerSubscriptionResponse:
        """The seller takes back a request that is still pending."""
        subscription = await self._repository.get_subscription(subscription_id, for_update=True)
        # The ownership check: another seller's subscription is "not found".
        if subscription is None or subscription.seller_id != seller_id:
            raise SellerSubscriptionNotFoundError()
        if subscription.status != SubscriptionStatus.PENDING:
            raise SubscriptionStatusConflictError("Only a pending request can be withdrawn")
        subscription.status = SubscriptionStatus.CANCELLED.value
        subscription.ended_by_account_id = withdrawn_by
        await self._session.commit()
        logger.info("plan request withdrawn", extra={"subscription_id": str(subscription.id)})
        return _subscription_response(subscription, utc_now())

    # ── Staff: subscriptions ─────────────────────────────────────────────

    async def list_all_subscriptions(
        self, pagination: PaginationParams, filters: StaffSubscriptionFilters
    ) -> Page[SellerSubscriptionResponse]:
        subscriptions, total = await self._repository.list_subscriptions(
            pagination,
            seller_id=filters.seller_id,
            plan_id=filters.plan_id,
            status=filters.status.value if filters.status else None,
        )
        return _subscription_page(subscriptions, total, pagination)

    async def activate(
        self,
        *,
        subscription_id: uuid.UUID,
        payment_reference: str | None,
        activated_by: uuid.UUID,
    ) -> SellerSubscriptionResponse:
        """Turn a pending request into a running (or scheduled) subscription,
        once the payment has been checked."""
        subscription = await self._existing(subscription_id)
        if subscription.status != SubscriptionStatus.PENDING:
            raise SubscriptionStatusConflictError("Only a pending request can be activated")
        await self._schedule(subscription, payment_reference, activated_by)
        return _subscription_response(subscription, utc_now())

    async def assign(
        self, *, payload: SubscriptionAssignRequest, assigned_by: uuid.UUID
    ) -> SellerSubscriptionResponse:
        """Give a plan to a seller directly, without a request from them."""
        # 404 unless the seller exists and is active.
        seller = await self._sellers.get_open_shop(payload.seller_id)
        plan = await self._offered_plan(payload.plan_id)
        subscription = _new_subscription(seller.id, plan, assigned_by)
        # Flushed inside _schedule together with its dates, so it never
        # exists as a second pending request.
        await self._schedule(subscription, payload.payment_reference, assigned_by, is_new=True)
        return _subscription_response(subscription, utc_now())

    async def reject(
        self, *, subscription_id: uuid.UUID, reason: str, rejected_by: uuid.UUID
    ) -> SellerSubscriptionResponse:
        subscription = await self._existing(subscription_id)
        if subscription.status != SubscriptionStatus.PENDING:
            raise SubscriptionStatusConflictError("Only a pending request can be rejected")
        subscription.status = SubscriptionStatus.REJECTED.value
        subscription.status_reason = reason
        subscription.decided_by_account_id = rejected_by
        subscription.decided_at = utc_now()
        await self._session.commit()
        logger.info(
            "plan request rejected",
            extra={"subscription_id": str(subscription.id), "by_account_id": str(rejected_by)},
        )
        return _subscription_response(subscription, utc_now())

    async def cancel(
        self, *, subscription_id: uuid.UUID, reason: str, cancelled_by: uuid.UUID
    ) -> SellerSubscriptionResponse:
        """End a running or scheduled subscription early. The seller is on the
        default rate from this moment (or on their next scheduled plan)."""
        subscription = await self._existing(subscription_id)
        now = utc_now()
        if subscription.status != SubscriptionStatus.ACTIVE or subscription.ends_at <= now:
            raise SubscriptionStatusConflictError(
                "Only a running or scheduled subscription can be cancelled"
            )
        _end(subscription, now, reason, cancelled_by)
        await self._session.commit()
        logger.info(
            "subscription cancelled",
            extra={"subscription_id": str(subscription.id), "by_account_id": str(cancelled_by)},
        )
        return _subscription_response(subscription, now)

    # ── Staff: default commission rate ───────────────────────────────────

    async def get_default_rate(self) -> DefaultCommissionRateResponse:
        now = utc_now()
        rate = await self._repository.get_default_rate(now)
        if rate is None:
            raise DefaultCommissionRateNotSetError()
        return _rate_response(rate, current_id=rate.id)

    async def list_default_rates(
        self, pagination: PaginationParams
    ) -> Page[DefaultCommissionRateResponse]:
        """Every rate ever set, newest first, including ones still to come."""
        current = await self._repository.get_default_rate(utc_now())
        rates, total = await self._repository.list_default_rates(pagination)
        items = [_rate_response(rate, current_id=current.id if current else None) for rate in rates]
        return Page[DefaultCommissionRateResponse].build(items, total, pagination)

    async def set_default_rate(
        self, *, payload: DefaultCommissionRateRequest, set_by: uuid.UUID
    ) -> DefaultCommissionRateResponse:
        """Set the rate for sellers without a plan, from now or from a future
        moment. A new row every time: past rates are never edited, and orders
        already created keep the rate they recorded."""
        now = utc_now()
        effective_from = payload.effective_from or now
        if effective_from < now - EFFECTIVE_FROM_TOLERANCE:
            raise EffectiveDateInPastError()
        rate = DefaultCommissionRate(
            rate=_two_places(payload.rate),
            effective_from=effective_from,
            note=payload.note or None,
            set_by_account_id=set_by,
        )
        try:
            await self._repository.add_default_rate(rate)
        except IntegrityError as exc:
            await self._session.rollback()
            raise EffectiveDateTakenError() from exc
        await self._session.commit()
        logger.info(
            "default commission rate set",
            extra={
                "rate": str(rate.rate),
                "effective_from": effective_from.isoformat(),
                "by_account_id": str(set_by),
            },
        )
        current = await self._repository.get_default_rate(utc_now())
        return _rate_response(rate, current_id=current.id if current else None)

    # ── Helpers ──────────────────────────────────────────────────────────

    async def _offered_plan(self, plan_id: uuid.UUID) -> SellerPlan:
        plan = await self.get_plan(plan_id)
        if plan.status != PlanStatus.ACTIVE:
            raise SellerPlanRetiredError()
        return plan

    async def _existing(self, subscription_id: uuid.UUID) -> SellerSubscription:
        subscription = await self._repository.get_subscription(subscription_id, for_update=True)
        if subscription is None:
            raise SellerSubscriptionNotFoundError()
        return subscription

    async def _schedule(
        self,
        subscription: SellerSubscription,
        payment_reference: str | None,
        decided_by: uuid.UUID,
        *,
        is_new: bool = False,
    ) -> None:
        """Give the subscription its period and make it active (README §10.2).

        - Nothing running or scheduled: it starts now.
        - The same plan is running or scheduled: it starts when that ends, so
          renewing early loses no paid days.
        - A different plan is running or scheduled: that is ended now, with
          no refund, and this one starts now.
        """
        now = utc_now()
        unfinished = await self._repository.list_unfinished_active(
            subscription.seller_id, now, for_update=True
        )
        starts_at = now
        if unfinished:
            last = unfinished[-1]
            if last.plan_id == subscription.plan_id:
                starts_at = last.ends_at
            else:
                for other in unfinished:
                    _end(other, now, REPLACED_REASON, decided_by)
                # The old periods must be shortened in the database before
                # the new one is written, or the two would overlap.
                await self._session.flush()

        subscription.status = SubscriptionStatus.ACTIVE.value
        subscription.starts_at = starts_at
        subscription.ends_at = starts_at + timedelta(days=subscription.duration_days)
        subscription.payment_reference = payment_reference
        subscription.decided_by_account_id = decided_by
        subscription.decided_at = now
        try:
            if is_new:
                await self._repository.add_subscription(subscription)
            await self._session.commit()
        except IntegrityError as exc:
            # The exclusion constraint refused an overlap: another change to
            # this seller's subscriptions got in first.
            await self._session.rollback()
            raise SubscriptionPeriodConflictError() from exc
        logger.info(
            "subscription activated",
            extra={
                "subscription_id": str(subscription.id),
                "seller_id": str(subscription.seller_id),
                "by_account_id": str(decided_by),
            },
        )

    async def _plan_page(
        self, pagination: PaginationParams, *, status: str | None
    ) -> Page[SellerPlanResponse]:
        plans, total = await self._repository.list_plans(pagination, status=status)
        items = [SellerPlanResponse.model_validate(plan) for plan in plans]
        return Page[SellerPlanResponse].build(items, total, pagination)


def _new_subscription(
    seller_id: uuid.UUID, plan: SellerPlan, requested_by: uuid.UUID
) -> SellerSubscription:
    """A pending subscription carrying a SNAPSHOT of the plan's terms."""
    return SellerSubscription(
        seller_id=seller_id,
        plan_id=plan.id,
        status=SubscriptionStatus.PENDING.value,
        plan_name=plan.name,
        price=plan.price,
        currency=plan.currency,
        duration_days=plan.duration_days,
        commission_rate=plan.commission_rate,
        requested_by_account_id=requested_by,
    )


def _end(subscription: SellerSubscription, now: datetime, reason: str, ended_by: uuid.UUID) -> None:
    """Stop an active subscription. One that has started keeps the period it
    actually ran; one that never started keeps its planned dates as a record."""
    if subscription.starts_at <= now:
        subscription.ends_at = now
    subscription.status = SubscriptionStatus.CANCELLED.value
    subscription.status_reason = reason
    subscription.ended_by_account_id = ended_by


def _two_places(amount: Decimal) -> Decimal:
    return amount.quantize(Decimal("0.01"))


def _is_applicable(subscription: SellerSubscription, now: datetime) -> bool:
    return (
        subscription.status == SubscriptionStatus.ACTIVE
        and subscription.starts_at <= now < subscription.ends_at
    )


def _subscription_response(
    subscription: SellerSubscription, now: datetime
) -> SellerSubscriptionResponse:
    return SellerSubscriptionResponse(
        id=subscription.id,
        seller_id=subscription.seller_id,
        plan_id=subscription.plan_id,
        plan_name=subscription.plan_name,
        price=subscription.price,
        currency=subscription.currency,
        duration_days=subscription.duration_days,
        commission_rate=subscription.commission_rate,
        status=subscription.status,
        starts_at=subscription.starts_at,
        ends_at=subscription.ends_at,
        is_applicable=_is_applicable(subscription, now),
        status_reason=subscription.status_reason,
        payment_reference=subscription.payment_reference,
        decided_at=subscription.decided_at,
        created_at=subscription.created_at,
    )


def _subscription_page(
    subscriptions: list[SellerSubscription], total: int, pagination: PaginationParams
) -> Page[SellerSubscriptionResponse]:
    now = utc_now()
    items = [_subscription_response(subscription, now) for subscription in subscriptions]
    return Page[SellerSubscriptionResponse].build(items, total, pagination)


def _rate_response(
    rate: DefaultCommissionRate, *, current_id: uuid.UUID | None
) -> DefaultCommissionRateResponse:
    return DefaultCommissionRateResponse(
        id=rate.id,
        rate=rate.rate,
        effective_from=rate.effective_from,
        note=rate.note,
        set_by_account_id=rate.set_by_account_id,
        created_at=rate.created_at,
        is_current=rate.id == current_id,
    )
