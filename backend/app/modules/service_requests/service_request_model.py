"""Persistence model for service requests.

Mirrors `docs/database/database_schema.dbml`; change both together.

The service's name, price, and shop name are a SNAPSHOT of what the buyer
saw when asking. The order created on acceptance charges that price.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.modules.orders.order_constants import (
    ADDRESS_PART_MAX_LENGTH,
    BUYER_NOTE_MAX_LENGTH,
    DELIVERY_ADDRESS_MAX_LENGTH,
    REASON_MAX_LENGTH,
    RECIPIENT_NAME_MAX_LENGTH,
)
from app.modules.products.product_constants import (
    DEFAULT_CURRENCY,
    PRICE_DECIMAL_PLACES,
    PRICE_MAX_DIGITS,
    PRODUCT_NAME_MAX_LENGTH,
    ServiceLocation,
)
from app.modules.service_requests.service_request_constants import ServiceRequestStatus


class ServiceRequest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A buyer asking a provider to do a service at a time and place. Once
    accepted it points at the order the buyer pays (README §7.5)."""

    __tablename__ = "service_requests"
    __table_args__ = (
        CheckConstraint(
            f"status IN ({', '.join(repr(s.value) for s in ServiceRequestStatus)})",
            name="status_valid",
        ),
        CheckConstraint("unit_price >= 0", name="price_not_negative"),
        # The order exists exactly when the request was accepted.
        CheckConstraint(
            "(status = 'accepted') = (order_id IS NOT NULL)", name="order_only_when_accepted"
        ),
        CheckConstraint(
            f"service_location IN ({', '.join(repr(s.value) for s in ServiceLocation)})",
            name="service_location_valid",
        ),
        # The buyer gives a place only for a service done at their place.
        CheckConstraint(
            "num_nonnulls(province, district, sector) IN (0, 3)", name="place_complete"
        ),
        CheckConstraint(
            "(district IS NOT NULL) = (service_location = 'at_customer')",
            name="place_matches_location",
        ),
        CheckConstraint("district IS NOT NULL OR address IS NULL", name="address_needs_place"),
        Index("ix_service_requests_buyer_account_id_created_at", "buyer_account_id", "created_at"),
        Index(
            "ix_service_requests_seller_id_status_created_at", "seller_id", "status", "created_at"
        ),
    )

    buyer_account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("accounts.id", ondelete="RESTRICT")
    )
    seller_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sellers.id", ondelete="RESTRICT"))
    # The listing asked for. A link back only; the snapshot below is what counts.
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), index=True
    )
    service_name: Mapped[str] = mapped_column(String(PRODUCT_NAME_MAX_LENGTH))
    seller_name: Mapped[str] = mapped_column(String(150))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(PRICE_MAX_DIGITS, PRICE_DECIMAL_PLACES))
    currency: Mapped[str] = mapped_column(
        String(3), default=DEFAULT_CURRENCY, server_default=DEFAULT_CURRENCY
    )

    # Where the service is done, from the listing when asked (README §7.5, V15).
    service_location: Mapped[str] = mapped_column(String(20))
    # When, whom to contact, and, for `at_customer` only, where; as the buyer
    # gave it.
    scheduled_for: Mapped[datetime]
    contact_name: Mapped[str] = mapped_column(String(RECIPIENT_NAME_MAX_LENGTH))
    contact_phone: Mapped[str] = mapped_column(String(20))
    province: Mapped[str | None] = mapped_column(String(ADDRESS_PART_MAX_LENGTH))
    district: Mapped[str | None] = mapped_column(String(ADDRESS_PART_MAX_LENGTH))
    sector: Mapped[str | None] = mapped_column(String(ADDRESS_PART_MAX_LENGTH))
    address: Mapped[str | None] = mapped_column(String(DELIVERY_ADDRESS_MAX_LENGTH))
    note: Mapped[str | None] = mapped_column(String(BUYER_NOTE_MAX_LENGTH))

    status: Mapped[str] = mapped_column(
        String(20),
        default=ServiceRequestStatus.REQUESTED.value,
        server_default=ServiceRequestStatus.REQUESTED.value,
    )
    # Why the provider declined, or why the buyer cancelled.
    status_reason: Mapped[str | None] = mapped_column(String(REASON_MAX_LENGTH))
    responded_by_account_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("accounts.id", ondelete="SET NULL")
    )
    responded_at: Mapped[datetime | None]
    cancelled_at: Mapped[datetime | None]
    # Set on acceptance. Unique: one request never makes two orders.
    order_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("orders.id", ondelete="RESTRICT"), unique=True
    )
