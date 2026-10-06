"""Data access for orders. No business rules, and no commits: the service
owns the transaction (AGENTS.md §13)."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.orders.order_constants import SellerOrderStatus
from app.modules.orders.order_model import (
    Order,
    OrderItem,
    SellerOrder,
    SellerOrderEvent,
    order_number_sequence,
)
from app.shared.responses.pagination import PaginationParams


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Orders ───────────────────────────────────────────────────────────

    async def next_order_number(self) -> int:
        return await self._session.scalar(select(order_number_sequence.next_value()))

    async def get_order(self, order_id: uuid.UUID, *, for_update: bool = False) -> Order | None:
        statement = select(Order).where(Order.id == order_id)
        if for_update:
            # Every status change of an order or one of its parts locks the
            # order row first, so they happen one at a time.
            statement = statement.with_for_update()
        return await self._session.scalar(statement)

    async def add_all(self, rows: list) -> None:
        self._session.add_all(rows)
        await self._session.flush()

    async def list_orders(
        self,
        pagination: PaginationParams,
        *,
        buyer_account_id: uuid.UUID | None = None,
        status: str | None = None,
        search: str | None = None,
    ) -> tuple[list[Order], int]:
        statement = select(Order)
        if buyer_account_id is not None:
            statement = statement.where(Order.buyer_account_id == buyer_account_id)
        if status is not None:
            statement = statement.where(Order.status == status)
        if search is not None:
            statement = statement.where(Order.order_number.icontains(search, autoescape=True))
        total = await self._session.scalar(select(func.count()).select_from(statement.subquery()))
        rows = await self._session.scalars(
            statement.order_by(Order.created_at.desc(), Order.id)
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
        return list(rows), total or 0

    # ── Seller orders ────────────────────────────────────────────────────

    async def get_seller_order(self, seller_order_id: uuid.UUID) -> SellerOrder | None:
        return await self._session.get(SellerOrder, seller_order_id)

    async def list_seller_orders_of(self, order_ids: list[uuid.UUID]) -> list[SellerOrder]:
        if not order_ids:
            return []
        rows = await self._session.scalars(
            select(SellerOrder)
            .where(SellerOrder.order_id.in_(order_ids))
            .order_by(SellerOrder.seller_name, SellerOrder.id)
        )
        return list(rows)

    async def list_shop_orders(
        self, pagination: PaginationParams, *, seller_id: uuid.UUID, status: str | None
    ) -> tuple[list[tuple[SellerOrder, Order]], int]:
        """A shop's PAID orders, newest first. Unpaid ones are not the
        seller's business yet (README §9.3)."""
        statement = (
            select(SellerOrder, Order)
            .join(Order, Order.id == SellerOrder.order_id)
            .where(
                SellerOrder.seller_id == seller_id,
                Order.paid_at.is_not(None),
                SellerOrder.status != SellerOrderStatus.AWAITING_PAYMENT.value,
            )
        )
        if status is not None:
            statement = statement.where(SellerOrder.status == status)
        total = await self._session.scalar(select(func.count()).select_from(statement.subquery()))
        rows = await self._session.execute(
            statement.order_by(Order.paid_at.desc(), SellerOrder.id)
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
        return [(row[0], row[1]) for row in rows], total or 0

    # ── Items and events ─────────────────────────────────────────────────

    async def list_items(self, seller_order_ids: list[uuid.UUID]) -> list[OrderItem]:
        if not seller_order_ids:
            return []
        rows = await self._session.scalars(
            select(OrderItem)
            .where(OrderItem.seller_order_id.in_(seller_order_ids))
            .order_by(OrderItem.product_name, OrderItem.id)
        )
        return list(rows)

    async def list_events(self, seller_order_ids: list[uuid.UUID]) -> list[SellerOrderEvent]:
        if not seller_order_ids:
            return []
        rows = await self._session.scalars(
            select(SellerOrderEvent)
            .where(SellerOrderEvent.seller_order_id.in_(seller_order_ids))
            .order_by(SellerOrderEvent.created_at, SellerOrderEvent.id)
        )
        return list(rows)
