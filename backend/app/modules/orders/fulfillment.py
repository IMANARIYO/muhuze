"""Seller-side order fulfillment (Phase 2): per-seller fulfillment + shipment.

A single buyer order is fanned out into one `seller_order` per distinct
seller the moment the money clears. Each seller then runs its own slice
through a tiny state machine:

    pending  ->  accepted  ->  shipped  ->  delivered
              ->  rejected
    any      ->  cancelled (admin override, not exposed via these endpoints)

`create_seller_orders_for_order` is called from the payment module inside the
same DB transaction as `Payment -> paid`, so a seller_order can never exist
for an unpaid order.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.orders.exceptions import (
    SellerOrderNotFoundError,
    SellerOrderStateError,
    ShipmentNotFoundError,
)
from app.modules.orders.models import Order, SellerOrder, SellerOrderStatus
from app.modules.orders.repository import (
    OrderItemRepository,
    SellerOrderRepository,
    ShipmentRepository,
)

_ALLOWED = SellerOrderStatus


def _require(
    seller_order: SellerOrder,
    *allowed: SellerOrderStatus,
) -> None:
    if seller_order.status not in allowed:
        raise SellerOrderStateError(
            f"Cannot move a '{seller_order.status}' seller order; "
            f"expected one of {', '.join(a.value for a in allowed)}"
        )


async def create_seller_orders_for_order(db: AsyncSession, order: Order) -> list[SellerOrder]:
    """Idempotently create one seller_order per distinct seller in the order."""
    items = await OrderItemRepository(db).list_for_order(order.id)
    seller_ids: set[uuid.UUID] = {item.seller_id for item in items}
    created: list[SellerOrder] = []
    repo = SellerOrderRepository(db)
    for seller_id in sorted(seller_ids):
        existing = await repo.get_for_order_seller(order.id, seller_id)
        if existing is None:
            created.append(await repo.create(order_id=order.id, seller_id=seller_id))
    return created


class FulfillmentService:
    """Seller actions over their fulfillment slices of an order."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.seller_orders = SellerOrderRepository(db)
        self.shipments = ShipmentRepository(db)

    async def list_for_seller(self, seller_id: uuid.UUID) -> list[SellerOrder]:
        return await self.seller_orders.list_for_seller(seller_id)

    async def accept(self, seller_id: uuid.UUID, seller_order_id: uuid.UUID) -> SellerOrder:
        so = await self._owned(seller_id, seller_order_id)
        _require(so, _ALLOWED.PENDING)
        return await self.seller_orders.update(
            so, status=_ALLOWED.ACCEPTED, accepted_at=datetime.now(UTC)
        )

    async def reject(
        self, seller_id: uuid.UUID, seller_order_id: uuid.UUID, reason: str
    ) -> SellerOrder:
        so = await self._owned(seller_id, seller_order_id)
        _require(so, _ALLOWED.PENDING)
        return await self.seller_orders.update(
            so, status=_ALLOWED.REJECTED, rejected_reason=reason
        )

    async def ship(
        self,
        seller_id: uuid.UUID,
        seller_order_id: uuid.UUID,
        *,
        carrier: str | None,
        tracking_number: str | None,
        notes: str | None,
    ) -> tuple[SellerOrder, object]:
        so = await self._owned(seller_id, seller_order_id)
        _require(so, _ALLOWED.ACCEPTED)
        now = datetime.now(UTC)
        shipment = await self.shipments.create(
            seller_order_id=so.id,
            carrier=carrier,
            tracking_number=tracking_number,
            notes=notes,
            status=_ALLOWED.SHIPPED,
            shipped_at=now,
        )
        updated = await self.seller_orders.update(
            so, status=_ALLOWED.SHIPPED, shipped_at=now
        )
        return updated, shipment

    async def deliver(self, shipment_id: uuid.UUID) -> SellerOrder:
        shipment = await self.shipments.get_by_id(shipment_id)
        if shipment is None:
            raise ShipmentNotFoundError()
        so = await self.seller_orders.get_by_id(shipment.seller_order_id)
        if so is None:
            raise SellerOrderNotFoundError()
        _require(so, _ALLOWED.SHIPPED)
        await self.shipments.mark_delivered(shipment, delivered_at=datetime.now(UTC))
        return await self.seller_orders.update(
            so, status=_ALLOWED.DELIVERED, delivered_at=datetime.now(UTC)
        )

    async def _owned(
        self, seller_id: uuid.UUID, seller_order_id: uuid.UUID
    ) -> SellerOrder:
        so = await self.seller_orders.get_by_id(seller_order_id)
        if so is None or so.seller_id != seller_id:
            raise SellerOrderNotFoundError()
        return so
