import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.orders.models import (
    Order,
    OrderItem,
    SellerOrder,
    Shipment,
    ShippingInfo,
)


class OrderRepository:
    """Data access for orders. No business rules here — those live in
    OrderService."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, order_id: uuid.UUID) -> Order | None:
        result = await self.db.execute(select(Order).where(Order.id == order_id))
        return result.scalar_one_or_none()

    async def get_by_order_number(self, order_number: str) -> Order | None:
        result = await self.db.execute(
            select(Order).where(Order.order_number == order_number)
        )
        return result.scalar_one_or_none()

    async def list_for_account(
        self, account_id: uuid.UUID
    ) -> list[Order]:
        result = await self.db.execute(
            select(Order)
            .where(Order.buyer_account_id == account_id)
            .order_by(Order.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_all(self) -> list[Order]:
        result = await self.db.execute(
            select(Order).order_by(Order.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(
        self,
        *,
        order_number: str,
        buyer_account_id: uuid.UUID,
        subtotal: float,
        shipping_fee: float,
        discount_amount: float,
        total_amount: float,
        currency: str,
        contact_phone: str | None,
        notes: str | None,
    ) -> Order:
        order = Order(
            order_number=order_number,
            buyer_account_id=buyer_account_id,
            subtotal=subtotal,
            shipping_fee=shipping_fee,
            discount_amount=discount_amount,
            total_amount=total_amount,
            currency=currency,
            contact_phone=contact_phone,
            notes=notes,
        )
        self.db.add(order)
        await self.db.flush()
        await self.db.refresh(order)
        return order

    async def update(
        self, order: Order, **changes
    ) -> Order:
        for field, value in changes.items():
            if value is not None:
                setattr(order, field, value)
        await self.db.flush()
        await self.db.refresh(order)
        return order

    async def flush_changes(self, order: Order) -> Order:
        """Persist an already-mutated order (attribute set directly on the
        ORM object) without going through the skip-None `update`."""
        await self.db.flush()
        await self.db.refresh(order)
        return order


class OrderItemRepository:
    """Data access for order items. No business rules here."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_for_order(self, order_id: uuid.UUID) -> list[OrderItem]:
        result = await self.db.execute(
            select(OrderItem)
            .where(OrderItem.order_id == order_id)
            .order_by(OrderItem.created_at.asc())
        )
        return list(result.scalars().all())

    async def list_for_seller_order(
        self, seller_id: uuid.UUID, order_id: uuid.UUID
    ) -> list[OrderItem]:
        result = await self.db.execute(
            select(OrderItem).where(
                OrderItem.order_id == order_id,
                OrderItem.seller_id == seller_id,
            )
        )
        return list(result.scalars().all())

    async def list_for_seller(self, seller_id: uuid.UUID) -> list[OrderItem]:
        result = await self.db.execute(
            select(OrderItem)
            .where(OrderItem.seller_id == seller_id)
            .order_by(OrderItem.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(
        self,
        *,
        order_id: uuid.UUID,
        seller_id: uuid.UUID,
        listing_id: uuid.UUID,
        product_variant_id: uuid.UUID,
        product_name: str,
        variant_name: str | None,
        unit_price: float,
        quantity: int,
        subtotal: float,
    ) -> OrderItem:
        item = OrderItem(
            order_id=order_id,
            seller_id=seller_id,
            listing_id=listing_id,
            product_variant_id=product_variant_id,
            product_name=product_name,
            variant_name=variant_name,
            unit_price=unit_price,
            quantity=quantity,
            subtotal=subtotal,
        )
        self.db.add(item)
        await self.db.flush()
        await self.db.refresh(item)
        return item


class ShippingInfoRepository:
    """Data access for order shipping snapshots. No business rules here."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_order(self, order_id: uuid.UUID) -> ShippingInfo | None:
        result = await self.db.execute(
            select(ShippingInfo).where(ShippingInfo.order_id == order_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        order_id: uuid.UUID,
        recipient_name: str,
        phone: str,
        country: str,
        province: str | None,
        district: str | None,
        sector: str | None,
        cell: str | None,
        village: str | None,
        address_line: str | None,
        delivery_instructions: str | None,
        latitude: float | None,
        longitude: float | None,
    ) -> ShippingInfo:
        info = ShippingInfo(
            order_id=order_id,
            recipient_name=recipient_name,
            phone=phone,
            country=country,
            province=province,
            district=district,
            sector=sector,
            cell=cell,
            village=village,
            address_line=address_line,
            delivery_instructions=delivery_instructions,
            latitude=latitude,
            longitude=longitude,
        )
        self.db.add(info)
        await self.db.flush()
        await self.db.refresh(info)
        return info

    async def set_order(self, info: ShippingInfo, *, order_id: uuid.UUID) -> ShippingInfo:
        info.order_id = order_id
        await self.db.flush()
        await self.db.refresh(info)
        return info


class SellerOrderRepository:
    """Data access for per-seller fulfillment records. No business rules here —
    the state machine lives in FulfillmentService."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, seller_order_id: uuid.UUID) -> SellerOrder | None:
        result = await self.db.execute(
            select(SellerOrder).where(SellerOrder.id == seller_order_id)
        )
        return result.scalar_one_or_none()

    async def get_for_order_seller(
        self, order_id: uuid.UUID, seller_id: uuid.UUID
    ) -> SellerOrder | None:
        result = await self.db.execute(
            select(SellerOrder).where(
                SellerOrder.order_id == order_id,
                SellerOrder.seller_id == seller_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_for_order(self, order_id: uuid.UUID) -> list[SellerOrder]:
        result = await self.db.execute(
            select(SellerOrder)
            .where(SellerOrder.order_id == order_id)
            .order_by(SellerOrder.seller_id)
        )
        return list(result.scalars().all())

    async def list_for_seller(self, seller_id: uuid.UUID) -> list[SellerOrder]:
        result = await self.db.execute(
            select(SellerOrder)
            .where(SellerOrder.seller_id == seller_id)
            .order_by(SellerOrder.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(
        self, *, order_id: uuid.UUID, seller_id: uuid.UUID
    ) -> SellerOrder:
        seller_order = SellerOrder(order_id=order_id, seller_id=seller_id)
        self.db.add(seller_order)
        await self.db.flush()
        await self.db.refresh(seller_order)
        return seller_order

    async def update(self, seller_order: SellerOrder, **changes) -> SellerOrder:
        for field, value in changes.items():
            if value is not None:
                setattr(seller_order, field, value)
        await self.db.flush()
        await self.db.refresh(seller_order)
        return seller_order


class ShipmentRepository:
    """Data access for shipments (deliveries of a seller_order)."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, shipment_id: uuid.UUID) -> Shipment | None:
        result = await self.db.execute(
            select(Shipment).where(Shipment.id == shipment_id)
        )
        return result.scalar_one_or_none()

    async def get_for_seller_order(self, seller_order_id: uuid.UUID) -> Shipment | None:
        result = await self.db.execute(
            select(Shipment).where(Shipment.seller_order_id == seller_order_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        seller_order_id: uuid.UUID,
        carrier: str | None,
        tracking_number: str | None,
        notes: str | None,
        status: str,
        shipped_at,
    ) -> Shipment:
        shipment = Shipment(
            seller_order_id=seller_order_id,
            carrier=carrier,
            tracking_number=tracking_number,
            notes=notes,
            status=status,
            shipped_at=shipped_at,
        )
        self.db.add(shipment)
        await self.db.flush()
        await self.db.refresh(shipment)
        return shipment

    async def mark_delivered(self, shipment: Shipment, *, delivered_at) -> Shipment:
        from app.modules.orders.models import SellerOrderStatus

        shipment.status = SellerOrderStatus.DELIVERED
        shipment.delivered_at = delivered_at
        await self.db.flush()
        await self.db.refresh(shipment)
        return shipment
