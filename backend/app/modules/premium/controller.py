import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.premium.models import PremiumPlan
from app.modules.premium.repository import (
    PremiumPlanRepository,
    SellerSubscriptionRepository,
)
from app.modules.premium.schemas import (
    PremiumPlanRequest,
    PremiumPlanResponse,
    PremiumPlanUpdateRequest,
    SellerSubscriptionResponse,
    SubscribeRequest,
    SubscriptionStatusResponse,
)
from app.modules.premium.service import PremiumService
from app.modules.sellers.models import Seller


class PremiumController:
    """Translates HTTP requests/responses to and from the premium services."""

    def __init__(self, db: AsyncSession) -> None:
        self.service = PremiumService(
            PremiumPlanRepository(db), SellerSubscriptionRepository(db)
        )

    # ── plans (public + admin) ────────────────────────────────────────

    async def list_available_plans(self) -> list[PremiumPlanResponse]:
        plans = await self.service.list_available_plans()
        return [PremiumPlanResponse.model_validate(plan) for plan in plans]

    async def create_plan(self, payload: PremiumPlanRequest) -> PremiumPlanResponse:
        plan = await self.service.create_plan(plan=_to_plan(payload))
        return PremiumPlanResponse.model_validate(plan)

    async def update_plan(
        self, plan_id: uuid.UUID, payload: PremiumPlanUpdateRequest
    ) -> PremiumPlanResponse:
        changes = payload.model_dump(exclude_unset=True)
        plan = await self.service.update_plan(plan_id, changes=changes)
        return PremiumPlanResponse.model_validate(plan)

    # ── subscriptions (seller self-service) ───────────────────────────

    async def subscribe(
        self, seller: Seller, payload: SubscribeRequest
    ) -> SellerSubscriptionResponse:
        subscription = await self.service.subscribe(seller.id, plan_id=payload.plan_id)
        return SellerSubscriptionResponse.model_validate(subscription)

    async def my_status(self, seller: Seller) -> SubscriptionStatusResponse:
        state = await self.service.my_status(seller.id)
        return SubscriptionStatusResponse(
            seller_id=state["seller_id"],
            is_premium=state["is_premium"],
            commission_rate=state["commission_rate"],
            subscription=(
                SellerSubscriptionResponse.model_validate(state["subscription"])
                if state["subscription"] is not None
                else None
            ),
        )

    async def my_subscription(self, seller: Seller) -> SellerSubscriptionResponse:
        subscription = await self.service.my_current_subscription(seller.id)
        return SellerSubscriptionResponse.model_validate(subscription)

    async def cancel(self, seller: Seller) -> SellerSubscriptionResponse:
        subscription = await self.service.cancel(seller.id)
        return SellerSubscriptionResponse.model_validate(subscription)

    async def my_history(self, seller: Seller) -> list[SellerSubscriptionResponse]:
        subscriptions = await self.service.my_history(seller.id)
        return [
            SellerSubscriptionResponse.model_validate(subscription)
            for subscription in subscriptions
        ]

    # ── subscriptions (admin) ─────────────────────────────────────────

    async def list_all_subscriptions(self) -> list[SellerSubscriptionResponse]:
        subscriptions = await self.service.list_all_subscriptions()
        return [
            SellerSubscriptionResponse.model_validate(subscription)
            for subscription in subscriptions
        ]


def _to_plan(payload: PremiumPlanRequest) -> PremiumPlan:
    return PremiumPlan(
        code=payload.code,
        name=payload.name,
        description=payload.description,
        price=payload.price,
        currency=payload.currency,
        duration_days=payload.duration_days,
        commission_rate=payload.commission_rate,
        listing_limit=payload.listing_limit,
        premium_badge=payload.premium_badge,
        unlimited_listings=payload.unlimited_listings,
        priority_notifications=payload.priority_notifications,
        early_promotion_access=payload.early_promotion_access,
        premium_only_promotions=payload.premium_only_promotions,
        premium_discounts=payload.premium_discounts,
        enhanced_favorites=payload.enhanced_favorites,
        priority_support=payload.priority_support,
        priority_service_handling=payload.priority_service_handling,
        referral_commission_eligible=payload.referral_commission_eligible,
        enhanced_visibility=payload.enhanced_visibility,
        promotional_advantages=payload.promotional_advantages,
        advanced_analytics=payload.advanced_analytics,
        seller_verification_eligible=payload.seller_verification_eligible,
        is_active=payload.is_active,
    )
