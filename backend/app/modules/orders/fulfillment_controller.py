import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.orders.fulfillment import FulfillmentService
from app.modules.orders.fulfillment_schemas import (
    SellerOrderResponse,
    ShipmentResponse,
)
from app.modules.orders.repository import ShipmentRepository
from app.modules.sellers.models import Seller


class FulfillmentController:
    """Translates seller HTTP requests/responses to/from FulfillmentService."""

    def __init__(self, db: AsyncSession) -> None:
        self.service = FulfillmentService(db)
        self.shipments = ShipmentRepository(db)

    async def list_my(self, seller: Seller) -> list[SellerOrderResponse]:
        rows = await self.service.list_for_seller(seller.id)
        return [await self._to_response(row) for row in rows]

    async def accept(self, seller: Seller, seller_order_id: uuid.UUID) -> SellerOrderResponse:
        row = await self.service.accept(seller.id, seller_order_id)
        return await self._to_response(row)

    async def reject(
        self, seller: Seller, seller_order_id: uuid.UUID, reason: str
    ) -> SellerOrderResponse:
        row = await self.service.reject(seller.id, seller_order_id, reason)
        return await self._to_response(row)

    async def ship(
        self,
        seller: Seller,
        seller_order_id: uuid.UUID,
        *,
        carrier: str | None,
        tracking_number: str | None,
        notes: str | None,
    ) -> SellerOrderResponse:
        row, _shipment = await self.service.ship(
            seller.id,
            seller_order_id,
            carrier=carrier,
            tracking_number=tracking_number,
            notes=notes,
        )
        return await self._to_response(row)

    async def deliver(
        self, seller: Seller, shipment_id: uuid.UUID
    ) -> SellerOrderResponse:
        shipment = await self.shipments.get_by_id(shipment_id)
        if shipment is None:
            row = None
        else:
            owned = await self.service.seller_orders.get_by_id(shipment.seller_order_id)
            row = owned if owned is not None and owned.seller_id == seller.id else None
        if row is None:
            from app.modules.orders.exceptions import SellerOrderNotFoundError

            raise SellerOrderNotFoundError()
        updated = await self.service.deliver(shipment.id)
        return await self._to_response(updated)

    async def _to_response(self, seller_order) -> SellerOrderResponse:
        response = SellerOrderResponse.model_validate(seller_order)
        shipment = await self.shipments.get_for_seller_order(seller_order.id)
        response.shipment = ShipmentResponse.model_validate(shipment) if shipment else None
        return response
