"""Data access for seller plans, subscriptions, and the default commission
rate. No business rules, and no commits: the service owns the transaction
(AGENTS.md §13)."""

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.seller_plans.seller_plan_constants import SubscriptionStatus
from app.modules.seller_plans.seller_plan_model import (
    DefaultCommissionRate,
    SellerPlan,
    SellerSubscription,
)
from app.shared.responses.pagination import PaginationParams

ACTIVE = SubscriptionStatus.ACTIVE.value


class SellerPlanRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Plans ────────────────────────────────────────────────────────────

    async def get_plan(self, plan_id: uuid.UUID) -> SellerPlan | None:
        return await self._session.get(SellerPlan, plan_id)

    async def get_plan_by_code(self, code: str) -> SellerPlan | None:
        return await self._session.scalar(select(SellerPlan).where(SellerPlan.code == code))

    async def add_plan(self, plan: SellerPlan) -> None:
        self._session.add(plan)
        await self._session.flush()

    async def delete_plan(self, plan: SellerPlan) -> None:
        await self._session.delete(plan)
        await self._session.flush()

    async def list_plans(
        self, pagination: PaginationParams, *, status: str | None
    ) -> tuple[list[SellerPlan], int]:
        statement = select(SellerPlan)
        if status is not None:
            statement = statement.where(SellerPlan.status == status)
        total = await self._session.scalar(select(func.count()).select_from(statement.subquery()))
        rows = await self._session.scalars(
            # Cheapest first, the order a seller compares them in.
            statement.order_by(SellerPlan.price, SellerPlan.name, SellerPlan.id)
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
        return list(rows), total or 0

    # ── Subscriptions ────────────────────────────────────────────────────

    async def get_subscription(
        self, subscription_id: uuid.UUID, *, for_update: bool = False
    ) -> SellerSubscription | None:
        statement = select(SellerSubscription).where(SellerSubscription.id == subscription_id)
        if for_update:
            statement = statement.with_for_update()
        return await self._session.scalar(statement)

    async def add_subscription(self, subscription: SellerSubscription) -> None:
        self._session.add(subscription)
        await self._session.flush()

    async def get_applicable(self, seller_id: uuid.UUID, at: datetime) -> SellerSubscription | None:
        """The subscription in force at `at`. The exclusion constraint
        guarantees there is at most one."""
        return await self._session.scalar(
            select(SellerSubscription).where(
                SellerSubscription.seller_id == seller_id,
                SellerSubscription.status == ACTIVE,
                SellerSubscription.starts_at <= at,
                SellerSubscription.ends_at > at,
            )
        )

    async def list_unfinished_active(
        self, seller_id: uuid.UUID, at: datetime, *, for_update: bool = False
    ) -> list[SellerSubscription]:
        """Active subscriptions that are running or still to start, in the
        order they run. Locked when a new one is about to be scheduled."""
        statement = (
            select(SellerSubscription)
            .where(
                SellerSubscription.seller_id == seller_id,
                SellerSubscription.status == ACTIVE,
                SellerSubscription.ends_at > at,
            )
            .order_by(SellerSubscription.starts_at)
        )
        if for_update:
            statement = statement.with_for_update()
        return list(await self._session.scalars(statement))

    async def get_pending(self, seller_id: uuid.UUID) -> SellerSubscription | None:
        return await self._session.scalar(
            select(SellerSubscription).where(
                SellerSubscription.seller_id == seller_id,
                SellerSubscription.status == SubscriptionStatus.PENDING.value,
            )
        )

    async def list_subscriptions(
        self,
        pagination: PaginationParams,
        *,
        seller_id: uuid.UUID | None = None,
        plan_id: uuid.UUID | None = None,
        status: str | None = None,
    ) -> tuple[list[SellerSubscription], int]:
        statement = select(SellerSubscription)
        if seller_id is not None:
            statement = statement.where(SellerSubscription.seller_id == seller_id)
        if plan_id is not None:
            statement = statement.where(SellerSubscription.plan_id == plan_id)
        if status is not None:
            statement = statement.where(SellerSubscription.status == status)
        total = await self._session.scalar(select(func.count()).select_from(statement.subquery()))
        rows = await self._session.scalars(
            statement.order_by(SellerSubscription.created_at.desc(), SellerSubscription.id)
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
        return list(rows), total or 0

    # ── Default commission rate ──────────────────────────────────────────

    async def get_default_rate(self, at: datetime) -> DefaultCommissionRate | None:
        """The rate in force at `at`: the latest one that has taken effect."""
        return await self._session.scalar(
            select(DefaultCommissionRate)
            .where(DefaultCommissionRate.effective_from <= at)
            .order_by(DefaultCommissionRate.effective_from.desc())
            .limit(1)
        )

    async def add_default_rate(self, rate: DefaultCommissionRate) -> None:
        self._session.add(rate)
        await self._session.flush()

    async def list_default_rates(
        self, pagination: PaginationParams
    ) -> tuple[list[DefaultCommissionRate], int]:
        total = await self._session.scalar(select(func.count()).select_from(DefaultCommissionRate))
        rows = await self._session.scalars(
            select(DefaultCommissionRate)
            .order_by(DefaultCommissionRate.effective_from.desc())
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
        return list(rows), total or 0
