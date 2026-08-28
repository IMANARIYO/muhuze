import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import Account
from app.modules.orders.fulfillment_schemas import SellerOrderResponse, ShipmentResponse
from app.modules.orders.repository import (
    OrderItemRepository,
    SellerOrderRepository,
    ShipmentRepository,
    ShippingInfoRepository,
)
from app.modules.orders.schemas import (
    CheckoutRequest,
    OrderDetailResponse,
    OrderSummaryResponse,
    ShippingInfoResponse,
)
from app.modules.orders.service import OrderService


class OrderController:
    """Translates HTTP requests/responses to and from the order service."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.service = OrderService(db)
        self.items_repo = OrderItemRepository(db)
        self.info_repo = ShippingInfoRepository(db)
        self.seller_order_repo = SellerOrderRepository(db)
        self.shipment_repo = ShipmentRepository(db)

    async def checkout(self, account: Account, payload: CheckoutRequest) -> OrderDetailResponse:
        order = await self.service.checkout(account.id, payload)
        return await self.get_detail(account, order.id)

    async def get_detail(self, account: Account, order_id: uuid.UUID) -> OrderDetailResponse:
        order = await self.service.get_order_detail(account.id, order_id)
        items = await self.items_repo.list_for_order(order.id)
        info = await self.info_repo.get_by_order(order.id)
        base = OrderDetailResponse.model_validate(order)
        base.items = items
        base.shipping = ShippingInfoResponse.model_validate(info) if info else None
        base.fulfillment = await self._fulfillment_for_order(order.id)
        return base

    async def receive(self, account: Account, order_id: uuid.UUID) -> OrderDetailResponse:
        order = await self.service.receive(account.id, order_id)
        return await self.get_detail(account, order.id)

    async def list_orders(self, account: Account) -> list[OrderSummaryResponse]:
        orders = await self.service.list_for_account(account.id)
        return [OrderSummaryResponse.model_validate(order) for order in orders]

    async def _fulfillment_for_order(self, order_id: uuid.UUID) -> list[SellerOrderResponse]:
        rows = await self.seller_order_repo.list_for_order(order_id)
        result: list[SellerOrderResponse] = []
        for row in rows:
            response = SellerOrderResponse.model_validate(row)
            shipment = await self.shipment_repo.get_for_seller_order(row.id)
            response.shipment = (
                ShipmentResponse.model_validate(shipment) if shipment else None
            )
            result.append(response)
        return result
