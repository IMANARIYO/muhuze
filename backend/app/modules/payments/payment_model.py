"""Persistence models for payments.

Mirrors `docs/database/database_schema.dbml`; change both together.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, String, false, text, true
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.modules.payments.payment_constants import (
    ACCOUNT_REFERENCE_MAX_LENGTH,
    DEFAULT_CURRENCY,
    INSTRUCTIONS_MAX_LENGTH,
    PAYER_NAME_MAX_LENGTH,
    PROVIDER_MAX_LENGTH,
    REASON_MAX_LENGTH,
    REFERENCE_MAX_LENGTH,
    REGISTERED_NAME_MAX_LENGTH,
    PaymentChannel,
    PaymentMethod,
    PaymentPurpose,
    PaymentStatus,
)


def _in_values(column: str, enum: type[StrEnum]) -> str:
    return f"{column} IN ({', '.join(repr(member.value) for member in enum)})"


class PaymentDestination(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """An account MUHUZE receives buyers' money on. Real numbers and names
    are data entered by staff; none is ever written in code. One that a
    payment has used is deactivated, never deleted."""

    __tablename__ = "payment_destinations"
    __table_args__ = (
        CheckConstraint(_in_values("method", PaymentMethod), name="method_valid"),
        CheckConstraint("NOT is_default OR is_active", name="default_is_active"),
        # At most one default per currency.
        Index(
            "uq_payment_destinations_currency_default",
            "currency",
            unique=True,
            postgresql_where=text("is_default"),
        ),
    )

    method: Mapped[str] = mapped_column(String(20))
    provider: Mapped[str] = mapped_column(String(PROVIDER_MAX_LENGTH))
    account_reference: Mapped[str] = mapped_column(String(ACCOUNT_REFERENCE_MAX_LENGTH))
    registered_name: Mapped[str] = mapped_column(String(REGISTERED_NAME_MAX_LENGTH))
    currency: Mapped[str] = mapped_column(
        String(3), default=DEFAULT_CURRENCY, server_default=DEFAULT_CURRENCY
    )
    instructions: Mapped[str | None] = mapped_column(String(INSTRUCTIONS_MAX_LENGTH))
    is_active: Mapped[bool] = mapped_column(default=True, server_default=true())
    is_default: Mapped[bool] = mapped_column(default=False, server_default=false())
    created_by_account_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("accounts.id", ondelete="SET NULL")
    )


class Payment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One attempt to pay for an order. An order can have several attempts,
    but only one can ever be paid.

    The destination_* columns are a snapshot of where the buyer was told to
    pay, so a later change to MUHUZE's accounts never rewrites the past.
    """

    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint(_in_values("status", PaymentStatus), name="status_valid"),
        CheckConstraint(_in_values("purpose", PaymentPurpose), name="purpose_valid"),
        CheckConstraint(_in_values("channel", PaymentChannel), name="channel_valid"),
        CheckConstraint("amount > 0", name="amount_positive"),
        # One paid payment per order, ever: the last line of defence against
        # an order being paid for twice (README §12.8).
        Index(
            "uq_payments_order_id_paid",
            "order_id",
            unique=True,
            postgresql_where=text("status = 'paid'"),
        ),
        # One attempt waiting for a decision per order.
        Index(
            "uq_payments_order_id_awaiting_verification",
            "order_id",
            unique=True,
            postgresql_where=text("status = 'awaiting_verification'"),
        ),
        # A transaction reference is used once, whatever its letter case.
        Index(
            "uq_payments_reference_lower",
            text("lower(reference)"),
            unique=True,
            postgresql_where=text("status <> 'rejected'"),
        ),
        Index("ix_payments_status_created_at", "status", "created_at"),
        Index("ix_payments_order_id", "order_id"),
    )

    purpose: Mapped[str] = mapped_column(
        String(20), default=PaymentPurpose.ORDER.value, server_default=PaymentPurpose.ORDER.value
    )
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id", ondelete="RESTRICT"))
    # Snapshot: what staff match against the statement.
    order_number: Mapped[str] = mapped_column(String(20))
    payer_account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("accounts.id", ondelete="RESTRICT")
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(3))
    channel: Mapped[str] = mapped_column(
        String(20), default=PaymentChannel.MANUAL.value, server_default=PaymentChannel.MANUAL.value
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default=PaymentStatus.AWAITING_VERIFICATION.value,
        server_default=PaymentStatus.AWAITING_VERIFICATION.value,
    )

    destination_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("payment_destinations.id", ondelete="RESTRICT")
    )
    destination_method: Mapped[str] = mapped_column(String(20))
    destination_provider: Mapped[str] = mapped_column(String(PROVIDER_MAX_LENGTH))
    destination_account_reference: Mapped[str] = mapped_column(String(ACCOUNT_REFERENCE_MAX_LENGTH))
    destination_registered_name: Mapped[str] = mapped_column(String(REGISTERED_NAME_MAX_LENGTH))

    # What the buyer told us.
    reference: Mapped[str] = mapped_column(String(REFERENCE_MAX_LENGTH))
    payer_name: Mapped[str | None] = mapped_column(String(PAYER_NAME_MAX_LENGTH))
    payer_phone: Mapped[str | None] = mapped_column(String(20))

    # What staff decided.
    verified_by_account_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("accounts.id", ondelete="SET NULL")
    )
    verified_at: Mapped[datetime | None]
    rejection_reason: Mapped[str | None] = mapped_column(String(REASON_MAX_LENGTH))
    paid_at: Mapped[datetime | None]
