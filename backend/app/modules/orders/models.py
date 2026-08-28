import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDPKMixin


class OrderStatus(StrEnum):
    """Customer-facing lifecycle of an order (Phase 1).

    Deliberately kept tiny: fulfillment (accept → ship → deliver → receive)
    is a *separate* state machine that lives on `seller_orders`, and money states live on `payment_status`. Phase 1 only tracks whether
    the order is live or cancelled before payment.
    """

    PENDING = "pending"
    CANCELLED = "cancelled"


class PaymentStatus(StrEnum):
    """Money state of the order, owned by the payments module and surfaced
    onto the order row."""

    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class Order(UUIDPKMixin, TimestampMixin, Base):
    """A customer's purchase.

    The order belongs to the **buyer**, never a seller. One checkout can span
    many sellers — each `order_item` carries its own `seller_id`, so the
    backend always knows who must fulfill what even though it reads as a
    single order to the customer.

    ALL money stored here is **gross** (what the buyer pays), captured as
    snapshots at checkout. The MUHUZE commission split is *derived* later in
    `revenue_transactions`, never stored redundantly here.

    `shipping_info_id` points at the immutable, order-owned `shipping_infos`
    snapshot; `shipping_address_id` is only a reference to which saved
    address was picked (for the customer's own memory) and is never used for
    actual delivery.
    """

    __tablename__ = "orders"

    order_number: Mapped[str] = mapped_column(
        String(30), unique=True, nullable=False, index=True
    )
    buyer_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=OrderStatus.PENDING, index=True
    )
    payment_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=PaymentStatus.PENDING, index=True
    )

    shipping_address_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shipping_addresses.id"),
        nullable=True,
    )
    shipping_info_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shipping_infos.id"),
        nullable=True,
    )

    contact_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    shipping_fee: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    discount_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="RWF")
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)

    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<Order {self.order_number} {self.status}/{self.payment_status}>"


class OrderItem(UUIDPKMixin, TimestampMixin, Base):
    """A single purchased line, snapshotted at checkout.

    The **transaction snapshot principle**: `product_name`, `variant_name`
    and `unit_price` are copied from the product/listing rows at purchase
    time rather than being live joins. Seller A sells a phone for 150000
    today and raises it to 170000 tomorrow — the completed order must still
    say 150000.

    `seller_id` drives the multi-seller split: which seller fulfills and earns
    this line.
    """

    __tablename__ = "order_items"

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id"),
        nullable=False,
        index=True,
    )
    seller_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sellers.id"),
        nullable=False,
        index=True,
    )
    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("seller_listings.id"),
        nullable=False,
        index=True,
    )
    product_variant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_variants.id"),
        nullable=False,
        index=True,
    )
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    variant_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    def __repr__(self) -> str:
        return f"<OrderItem order={self.order_id} {self.product_name!r} x{self.quantity}>"


class ShippingInfo(UUIDPKMixin, TimestampMixin, Base):
    """The immutable, order-owned snapshot of the delivery destination.

    Copied from the chosen `shipping_addresses` row at checkout. Later edits
    to the address book must never change past orders, so the order's
    delivery details live here, frozen, forever.
    """

    __tablename__ = "shipping_infos"

    order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id"),
        nullable=True,
        index=True,
    )
    recipient_name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    country: Mapped[str] = mapped_column(String(60), nullable=False, default="Rwanda")
    province: Mapped[str | None] = mapped_column(String(100), nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sector: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cell: Mapped[str | None] = mapped_column(String(100), nullable=True)
    village: Mapped[str | None] = mapped_column(String(100), nullable=True)
    address_line: Mapped[str | None] = mapped_column(String(255), nullable=True)
    delivery_instructions: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)

    def __repr__(self) -> str:
        return f"<ShippingInfo order={self.order_id} recipient={self.recipient_name!r}>"


class SellerOrderStatus(StrEnum):
    """Fulfillment lifecycle of a seller's *slice* of an order.

    One `seller_order` is created per (order, seller) the moment the money
    clears (`Payment -> paid`), so it only ever exists for a paid order. The
    buyer keeps seeing a single order; this per-seller copy is how each seller
    tracks and fulfills their share.

        pending  ->  accepted  ->  shipped  ->  delivered
                  ->  rejected
        any      ->  cancelled (admin override)
    """

    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class SellerOrder(UUIDPKMixin, TimestampMixin, Base):
    """A seller's fulfillment record for one buyer order.

    `order_id` + `seller_id` is unique: exactly one seller_order per seller on
    a given order, covering all of that seller's `order_items` lines. Created
    only after the order is paid. `rejected_reason` documents a rejection.
    """

    __tablename__ = "seller_orders"
    __table_args__ = (
        UniqueConstraint(
            "order_id", "seller_id", name="uq_seller_orders_order_seller"
        ),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id"),
        nullable=False,
        index=True,
    )
    seller_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sellers.id"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=SellerOrderStatus.PENDING, index=True
    )
    rejected_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    shipped_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<SellerOrder order={self.order_id} seller={self.seller_id} {self.status}>"


class Shipment(UUIDPKMixin, TimestampMixin, Base):
    """A physical delivery created when a seller ships a seller_order.

    One shipment per seller_order (a seller may ship a single seller's slice
    in one parcel). `carrier` / `tracking_number` are free-form for now.
    """

    __tablename__ = "shipments"

    seller_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("seller_orders.id"),
        nullable=False,
        index=True,
    )
    carrier: Mapped[str | None] = mapped_column(String(60), nullable=True)
    tracking_number: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=SellerOrderStatus.SHIPPED, index=True
    )
    shipped_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Shipment seller_order={self.seller_order_id} {self.status}>"
