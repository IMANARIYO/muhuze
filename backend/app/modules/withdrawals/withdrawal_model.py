"""Persistence models for withdrawal payouts and withdrawal requests.

Mirrors `docs/database/database_schema.dbml`; change both together.

A withdrawal is never deleted: it is an append-only financial record whose
status moves forward. Its destination_* columns snapshot where the payout
went, so a later edit to the destination never rewrites history
(README §14, invariant 22).
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.modules.withdrawals.withdrawal_constants import (
    ACCOUNT_NAME_MAX_LENGTH,
    ACCOUNT_NUMBER_MAX_LENGTH,
    DEFAULT_CURRENCY,
    PAYOUT_REFERENCE_MAX_LENGTH,
    PROVIDER_MAX_LENGTH,
    REASON_MAX_LENGTH,
    PayoutDestinationType,
    WithdrawalStatus,
)

Money = Numeric(14, 2)


def _in_values(column: str, enum: type) -> str:
    return f"{column} IN ({', '.join(repr(member.value) for member in enum)})"


class SellerPayoutDestination(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Where one seller receives withdrawals: mobile money or a bank account,
    stored as data only. Completely separate from MUHUZE's payment
    destinations (README §14, invariant 23). One that a withdrawal has used
    is deactivated, never deleted."""

    __tablename__ = "seller_payout_destinations"
    __table_args__ = (
        CheckConstraint(_in_values("type", PayoutDestinationType), name="type_valid"),
        Index("ix_seller_payout_destinations_seller_id", "seller_id"),
    )

    seller_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sellers.id", ondelete="RESTRICT"))
    type: Mapped[str] = mapped_column(String(20))
    provider: Mapped[str] = mapped_column(String(PROVIDER_MAX_LENGTH))
    account_number: Mapped[str] = mapped_column(String(ACCOUNT_NUMBER_MAX_LENGTH))
    account_name: Mapped[str] = mapped_column(String(ACCOUNT_NAME_MAX_LENGTH))
    is_active: Mapped[bool] = mapped_column(default=True)


class Withdrawal(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One request to be paid out from a seller's available balance."""

    __tablename__ = "withdrawals"
    __table_args__ = (
        CheckConstraint(_in_values("status", WithdrawalStatus), name="status_valid"),
        CheckConstraint("amount > 0", name="amount_positive"),
        Index("ix_withdrawals_status_created_at", "status", "created_at"),
        Index("ix_withdrawals_seller_id", "seller_id"),
    )

    seller_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sellers.id", ondelete="RESTRICT"))
    payout_destination_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("seller_payout_destinations.id", ondelete="RESTRICT")
    )
    amount: Mapped[Decimal] = mapped_column(Money)
    currency: Mapped[str] = mapped_column(
        String(3), default=DEFAULT_CURRENCY, server_default=DEFAULT_CURRENCY
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default=WithdrawalStatus.PENDING.value,
        server_default=WithdrawalStatus.PENDING.value,
    )

    # Snapshot of the destination at request time.
    destination_type: Mapped[str] = mapped_column(String(20))
    destination_provider: Mapped[str] = mapped_column(String(PROVIDER_MAX_LENGTH))
    destination_account_number: Mapped[str] = mapped_column(String(ACCOUNT_NUMBER_MAX_LENGTH))
    destination_account_name: Mapped[str] = mapped_column(String(ACCOUNT_NAME_MAX_LENGTH))

    # What staff decided.
    reason: Mapped[str | None] = mapped_column(String(REASON_MAX_LENGTH))
    payout_reference: Mapped[str | None] = mapped_column(String(PAYOUT_REFERENCE_MAX_LENGTH))
    reviewed_by_account_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("accounts.id", ondelete="SET NULL")
    )
    reviewed_at: Mapped[datetime | None]
    completed_at: Mapped[datetime | None]
