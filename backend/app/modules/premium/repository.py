import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.premium.models import (
    PremiumPlan,
    SellerSubscription,
    SubscriptionStatus,
)


class PremiumPlanRepository:
    """Data access for premium plans. No business rules here — those live in
    PremiumService."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, plan_id: uuid.UUID) -> PremiumPlan | None:
        result = await self.db.execute(
            select(PremiumPlan).where(PremiumPlan.id == plan_id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> PremiumPlan | None:
        result = await self.db.execute(
            select(PremiumPlan).where(PremiumPlan.code == code)
        )
        return result.scalar_one_or_none()

    async def list_active(self) -> list[PremiumPlan]:
        result = await self.db.execute(
            select(PremiumPlan)
            .where(PremiumPlan.is_active.is_(True))
            .order_by(PremiumPlan.price.asc())
        )
        return list(result.scalars().all())

    async def list_all(self) -> list[PremiumPlan]:
        result = await self.db.execute(
            select(PremiumPlan).order_by(PremiumPlan.created_at.asc())
        )
        return list(result.scalars().all())

    async def create(self, *, plan: PremiumPlan) -> PremiumPlan:
        self.db.add(plan)
        await self.db.flush()
        await self.db.refresh(plan)
        return plan

    async def update(self, plan: PremiumPlan, **changes) -> PremiumPlan:
        for field, value in changes.items():
            setattr(plan, field, value)
        await self.db.flush()
        await self.db.refresh(plan)
        return plan


class SellerSubscriptionRepository:
    """Data access for seller subscriptions. No business rules here — the
    "one active at a time" and commission-snapshot rules live in
    PremiumService."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, subscription_id: uuid.UUID) -> SellerSubscription | None:
        result = await self.db.execute(
            select(SellerSubscription).where(
                SellerSubscription.id == subscription_id
            )
        )
        return result.scalar_one_or_none()

    async def get_active_for_seller(
        self, seller_id: uuid.UUID
    ) -> SellerSubscription | None:
        result = await self.db.execute(
            select(SellerSubscription).where(
                SellerSubscription.seller_id == seller_id,
                SellerSubscription.status == SubscriptionStatus.ACTIVE,
            )
        )
        return result.scalar_one_or_none()

    async def list_for_seller(self, seller_id: uuid.UUID) -> list[SellerSubscription]:
        result = await self.db.execute(
            select(SellerSubscription)
            .where(SellerSubscription.seller_id == seller_id)
            .order_by(SellerSubscription.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_all(self) -> list[SellerSubscription]:
        result = await self.db.execute(
            select(SellerSubscription).order_by(
                SellerSubscription.created_at.desc()
            )
        )
        return list(result.scalars().all())

    async def create(
        self,
        *,
        seller_id: uuid.UUID,
        plan_id: uuid.UUID,
        commission_rate: float,
        starts_at,
        expires_at,
    ) -> SellerSubscription:
        subscription = SellerSubscription(
            seller_id=seller_id,
            plan_id=plan_id,
            status=SubscriptionStatus.ACTIVE,
            commission_rate=commission_rate,
            starts_at=starts_at,
            expires_at=expires_at,
        )
        self.db.add(subscription)
        await self.db.flush()
        await self.db.refresh(subscription)
        return subscription

    async def mark_expired(self, subscription: SellerSubscription) -> None:
        """Close out a prior `active` subscription when a new one replaces
        it (status → expired). Doesn't set cancelled_at — the term was
        replaced, not cancelled."""
        if subscription.status == SubscriptionStatus.ACTIVE:
            subscription.status = SubscriptionStatus.EXPIRED
            await self.db.flush()

    async def mark_cancelled(self, subscription: SellerSubscription, *, cancelled_at) -> None:
        subscription.status = SubscriptionStatus.CANCELLED
        subscription.cancelled_at = cancelled_at
        await self.db.flush()
