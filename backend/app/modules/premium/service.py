import uuid
from datetime import UTC, datetime, timedelta

from app.core.database import ensure_aware
from app.modules.premium.exceptions import (
    NoActiveSubscriptionError,
    PlanCodeTakenError,
    PremiumPlanNotFoundError,
    PremiumPlanNotPurchasableError,
)
from app.modules.premium.models import PremiumPlan, SellerSubscription
from app.modules.premium.repository import (
    PremiumPlanRepository,
    SellerSubscriptionRepository,
)

# ── the rates ─────────────────────────────────────────────────────────
# A seller who is NOT subscribed (basic) pays this percentage of every sale
# to MUHUZE. A seller with an active subscription pays the plan's
# `commission_rate` (seeded as 7%). Everything downstream that deducts
# commission should ask this module which rate applies, rather than
# hardcoding either number.
BASIC_COMMISSION_RATE = 12.0


def _default_plans() -> list[PremiumPlan]:
    """Seed data mirrors the old project's plans (see premiumPlans.ts):
    Monthly $10 / 30d and Annual $100 / 365d, both with a 7% commission
    rate while subscribed."""
    monthly = PremiumPlan(
        code="premium-monthly",
        name="Monthly",
        description="Monthly premium: 7% commission on every sale.",
        price=10,
        currency="USD",
        duration_days=30,
        commission_rate=7,
        listing_limit=0,
        premium_badge=True,
        unlimited_listings=True,
        priority_notifications=True,
        early_promotion_access=True,
        premium_only_promotions=True,
        premium_discounts=True,
        enhanced_favorites=True,
        priority_support=True,
        priority_service_handling=True,
        referral_commission_eligible=True,
        enhanced_visibility=True,
        promotional_advantages=True,
        advanced_analytics=True,
        seller_verification_eligible=True,
        is_active=True,
    )
    annual = PremiumPlan(
        code="premium-annual",
        name="Annual",
        description="Annual premium: 7% commission on every sale.",
        price=100,
        currency="USD",
        duration_days=365,
        commission_rate=7,
        listing_limit=0,
        premium_badge=True,
        unlimited_listings=True,
        priority_notifications=True,
        early_promotion_access=True,
        premium_only_promotions=True,
        premium_discounts=True,
        enhanced_favorites=True,
        priority_support=True,
        priority_service_handling=True,
        referral_commission_eligible=True,
        enhanced_visibility=True,
        promotional_advantages=True,
        advanced_analytics=True,
        seller_verification_eligible=True,
        is_active=True,
    )
    return [monthly, annual]


async def seed_default_premium_plans(repository: PremiumPlanRepository) -> int:
    """Idempotent: creates the default plans if their codes don't yet exist.
    Never overwrites an existing plan. Returns how many plans were created."""
    created = 0
    for plan in _default_plans():
        if await repository.get_by_code(plan.code) is None:
            await repository.create(plan=plan)
            created += 1
    return created


class PremiumService:
    """Business rules for premium plans and seller subscriptions.

    The central contract for commission: call `get_commission_state(seller_id)`
    (or the lighter `get_commission_rate`) to learn whether the seller is
    premium and which rate MUHUZE should deduct — this is what orders /
    revenue should use when taking their cut.
    """

    def __init__(
        self,
        plans: PremiumPlanRepository,
        subscriptions: SellerSubscriptionRepository,
    ) -> None:
        self.plans = plans
        self.subscriptions = subscriptions

    # ── public reads ──────────────────────────────────────────────────

    async def list_available_plans(self) -> list[PremiumPlan]:
        return await self.plans.list_active()

    async def get_plan(self, plan_id: uuid.UUID) -> PremiumPlan:
        plan = await self.plans.get_by_id(plan_id)
        if plan is None:
            raise PremiumPlanNotFoundError()
        return plan

    # ── admin plan management ─────────────────────────────────────────

    async def create_plan(self, *, plan: PremiumPlan) -> PremiumPlan:
        if await self.plans.get_by_code(plan.code) is not None:
            raise PlanCodeTakenError()
        return await self.plans.create(plan=plan)

    async def update_plan(
        self, plan_id: uuid.UUID, *, changes: dict
    ) -> PremiumPlan:
        """Apply a partial update to a plan (e.g. change `commission_rate`
        or `is_active`). A change of `code` is checked for uniqueness.
        Note: changing `commission_rate` affects *future* subscriptions
        only — existing subscriptions keep their purchase-time snapshot."""
        plan = await self.get_plan(plan_id)
        new_code = changes.get("code")
        if (
            new_code is not None
            and new_code != plan.code
            and await self.plans.get_by_code(new_code) is not None
        ):
            raise PlanCodeTakenError()
        await self.plans.update(plan, **changes)
        return plan

    # ── subscribing ───────────────────────────────────────────────────

    async def subscribe(
        self, seller_id: uuid.UUID, *, plan_id: uuid.UUID
    ) -> SellerSubscription:
        plan = await self.get_plan(plan_id)
        if not plan.is_active:
            raise PremiumPlanNotPurchasableError()

        now = datetime.now(UTC)
        # Buying closes out any currently-active subscription so a seller
        # only ever has one live at a time (history is preserved via the
        # now-expired row).
        current = await self.subscriptions.get_active_for_seller(seller_id)
        if current is not None:
            await self.subscriptions.mark_expired(current)

        return await self.subscriptions.create(
            seller_id=seller_id,
            plan_id=plan.id,
            commission_rate=float(plan.commission_rate),
            starts_at=now,
            expires_at=now + timedelta(days=plan.duration_days),
        )

    # ── cancellation ──────────────────────────────────────────────────

    async def cancel(self, seller_id: uuid.UUID) -> SellerSubscription:
        subscription = await self.subscriptions.get_active_for_seller(seller_id)
        if subscription is None:
            raise NoActiveSubscriptionError()
        await self.subscriptions.mark_cancelled(
            subscription, cancelled_at=datetime.now(UTC)
        )
        return subscription

    # ── commission & status ───────────────────────────────────────────

    async def get_commission_state(
        self, seller_id: uuid.UUID
    ) -> tuple[bool, float, SellerSubscription | None]:
        """Reusable helper other modules call at commission-deduction time.

        Returns (is_premium, commission_rate, active_subscription). A seller
        is premium when they hold an `active` subscription whose `expires_at`
        is still in the future; a row that's passed expiry is lazily marked
        `expired` and counted as basic (12%). 'is_premium' today defines the
        rate: 7% on the active plan, else 12% basic — see
        BASIC_COMMISSION_RATE."""
        subscription = await self.subscriptions.get_active_for_seller(seller_id)
        if subscription is not None:
            expires_at = ensure_aware(subscription.expires_at)
            if expires_at > datetime.now(UTC):
                return True, float(subscription.commission_rate), subscription
            # Lazy expiry: the row looks `active` but its term has ended.
            await self.subscriptions.mark_expired(subscription)
        return False, BASIC_COMMISSION_RATE, None

    async def get_commission_rate(self, seller_id: uuid.UUID) -> float:
        """Lightweight `get_commission_state` for callers that only need the
        percentage."""
        _, rate, _ = await self.get_commission_state(seller_id)
        return rate

    # ── seller self-service reads ─────────────────────────────────────

    async def my_status(self, seller_id: uuid.UUID) -> dict:
        is_premium, rate, subscription = await self.get_commission_state(seller_id)
        return {
            "seller_id": seller_id,
            "is_premium": is_premium,
            "commission_rate": rate,
            "subscription": subscription,
        }

    async def my_current_subscription(
        self, seller_id: uuid.UUID
    ) -> SellerSubscription:
        subscription = await self.subscriptions.get_active_for_seller(seller_id)
        if subscription is None:
            raise NoActiveSubscriptionError()
        # Same lazy-expiry treatment as get_commission_state.
        if ensure_aware(subscription.expires_at) <= datetime.now(UTC):
            await self.subscriptions.mark_expired(subscription)
            raise NoActiveSubscriptionError()
        return subscription

    async def my_history(self, seller_id: uuid.UUID) -> list[SellerSubscription]:
        return await self.subscriptions.list_for_seller(seller_id)

    # ── admin reads ───────────────────────────────────────────────────

    async def list_all_subscriptions(self) -> list[SellerSubscription]:
        return await self.subscriptions.list_all()
