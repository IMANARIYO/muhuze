"""Persistence models for orders.

Mirrors `docs/database/database_schema.dbml`; change both together.

Everything about price, product, and commission on these rows is a SNAPSHOT
taken when the order was created. It is never recalculated from current data
(README §11).
"""

import uuid
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    Sequence,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.modules.orders.order_constants import (
    ADDRESS_PART_MAX_LENGTH,
    BUYER_NOTE_MAX_LENGTH,
    DEFAULT_CURRENCY,
    DELIVERY_ADDRESS_MAX_LENGTH,
    IMAGE_URL_MAX_LENGTH,
    ORDER_NUMBER_SEQUENCE,
    REASON_MAX_LENGTH,
    RECIPIENT_NAME_MAX_LENGTH,
    OrderStatus,
    SellerOrderStatus,
)

Money = Numeric(14, 2)

# Order numbers come from here, so two orders can never share one. A rolled
# back order leaves a gap in the numbering, which is harmless.
order_number_sequence = Sequence(ORDER_NUMBER_SEQUENCE, metadata=Base.metadata)


def _in_values(column: str, enum: type[StrEnum]) -> str:
    return f"{column} IN ({', '.join(repr(member.value) for member in enum)})"


class Order(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """The buyer's whole purchase, and the thing a payment pays for."""

    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint(_in_values("status", OrderStatus), name="status_valid"),
        CheckConstraint("total_amount >= 0", name="total_not_negative"),
        Index("ix_orders_buyer_account_id_created_at", "buyer_account_id", "created_at"),
    )

    order_number: Mapped[str] = mapped_column(String(20), unique=True)
    buyer_account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("accounts.id", ondelete="RESTRICT")
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default=OrderStatus.AWAITING_PAYMENT.value,
        server_default=OrderStatus.AWAITING_PAYMENT.value,
    )
    currency: Mapped[str] = mapped_column(
        String(3), default=DEFAULT_CURRENCY, server_default=DEFAULT_CURRENCY
    )
    total_amount: Mapped[Decimal] = mapped_column(Money)

    # Where to deliver, as typed at checkout.
    recipient_name: Mapped[str] = mapped_column(String(RECIPIENT_NAME_MAX_LENGTH))
    recipient_phone: Mapped[str] = mapped_column(String(20))
    delivery_province: Mapped[str] = mapped_column(String(ADDRESS_PART_MAX_LENGTH))
    delivery_district: Mapped[str] = mapped_column(String(ADDRESS_PART_MAX_LENGTH))
    delivery_sector: Mapped[str] = mapped_column(String(ADDRESS_PART_MAX_LENGTH))
    delivery_address: Mapped[str | None] = mapped_column(String(DELIVERY_ADDRESS_MAX_LENGTH))
    buyer_note: Mapped[str | None] = mapped_column(String(BUYER_NOTE_MAX_LENGTH))

    # Set by the payments feature when the payment is confirmed.
    paid_at: Mapped[datetime | None]
    cancelled_at: Mapped[datetime | None]
    cancel_reason: Mapped[str | None] = mapped_column(String(REASON_MAX_LENGTH))


class SellerOrder(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One shop's part of an order: its own status, and its own money split."""

    __tablename__ = "seller_orders"
    __table_args__ = (
        UniqueConstraint("order_id", "seller_id"),
        Index("ix_seller_orders_seller_id_status_created_at", "seller_id", "status", "created_at"),
        CheckConstraint(_in_values("status", SellerOrderStatus), name="status_valid"),
        CheckConstraint(
            "subtotal >= 0 AND commission_amount >= 0 AND seller_amount >= 0",
            name="amounts_not_negative",
        ),
        # The split always adds up to what the buyer paid this seller.
        CheckConstraint("commission_amount + seller_amount = subtotal", name="split_adds_up"),
        # The rate came from exactly one place, and that place is recorded.
        CheckConstraint(
            "(terms_source = 'subscription' AND subscription_id IS NOT NULL"
            " AND default_rate_id IS NULL)"
            " OR (terms_source = 'default' AND default_rate_id IS NOT NULL"
            " AND subscription_id IS NULL)",
            name="terms_source_recorded",
        ),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id", ondelete="RESTRICT"))
    seller_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sellers.id", ondelete="RESTRICT"))
    seller_name: Mapped[str] = mapped_column(String(150))
    status: Mapped[str] = mapped_column(
        String(20),
        default=SellerOrderStatus.AWAITING_PAYMENT.value,
        server_default=SellerOrderStatus.AWAITING_PAYMENT.value,
    )
    status_reason: Mapped[str | None] = mapped_column(String(REASON_MAX_LENGTH))

    subtotal: Mapped[Decimal] = mapped_column(Money)
    commission_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    commission_amount: Mapped[Decimal] = mapped_column(Money)
    seller_amount: Mapped[Decimal] = mapped_column(Money)
    terms_source: Mapped[str] = mapped_column(String(20))
    subscription_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("seller_subscriptions.id", ondelete="RESTRICT")
    )
    plan_name: Mapped[str | None] = mapped_column(String(100))
    default_rate_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("default_commission_rates.id", ondelete="RESTRICT")
    )


class OrderItem(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """One product in an order, with what it was when it was bought. The
    product_id is only a link back; the snapshot columns are what count."""

    __tablename__ = "order_items"
    __table_args__ = (
        UniqueConstraint("seller_order_id", "product_id"),
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint("line_total = unit_price * quantity", name="line_total_correct"),
    )

    seller_order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("seller_orders.id", ondelete="CASCADE"), index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"))
    product_name: Mapped[str] = mapped_column(String(200))
    unit_price: Mapped[Decimal] = mapped_column(Money)
    quantity: Mapped[int]
    line_total: Mapped[Decimal] = mapped_column(Money)
    image_url: Mapped[str | None] = mapped_column(String(IMAGE_URL_MAX_LENGTH))
    # [{"name": "Storage", "value": 256, "unit": "GB"}, …]: display only.
    attributes: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)


class SellerOrderEvent(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Append-only: one row per status change of a seller order."""

    __tablename__ = "seller_order_events"

    seller_order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("seller_orders.id", ondelete="CASCADE"), index=True
    )
    from_status: Mapped[str | None] = mapped_column(String(20))
    to_status: Mapped[str] = mapped_column(String(20))
    reason: Mapped[str | None] = mapped_column(String(REASON_MAX_LENGTH))
    # Null when the system did it (payment confirmed).
    actor_account_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("accounts.id", ondelete="SET NULL")
    )
