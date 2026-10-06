"""Persistence models for revenue records and seller wallets.

Mirrors `docs/database/database_schema.dbml`; change both together.

These are financial records. They are append-only: a movement is never
edited or deleted to undo it; a new, reversing movement is written instead
(README §13.7, §14).
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.modules.wallets.wallet_constants import DEFAULT_CURRENCY, WalletTransactionKind

Money = Numeric(14, 2)


class RevenueTransaction(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """The accounting of ONE seller order's sale: how the buyer's money for
    that shop is shared between the seller and MUHUZE. Written once, when the
    payment is confirmed, from the amounts frozen on the seller order.

    It is also the seller's earning: `seller_amount` is what MUHUZE owes the
    seller for this sale (README §13.3).
    """

    __tablename__ = "revenue_transactions"
    __table_args__ = (
        CheckConstraint(
            "gross_amount >= 0 AND commission_amount >= 0 AND seller_amount >= 0",
            name="amounts_not_negative",
        ),
        CheckConstraint("commission_amount + seller_amount = gross_amount", name="split_adds_up"),
    )

    # UNIQUE: one revenue record per seller order, ever (README §14, invariant 1).
    seller_order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("seller_orders.id", ondelete="RESTRICT"), unique=True
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="RESTRICT"), index=True
    )
    seller_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sellers.id", ondelete="RESTRICT"), index=True
    )
    gross_amount: Mapped[Decimal] = mapped_column(Money)
    commission_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    commission_amount: Mapped[Decimal] = mapped_column(Money)
    seller_amount: Mapped[Decimal] = mapped_column(Money)
    currency: Mapped[str] = mapped_column(String(3))
    # Set if the sale was undone. The row itself is never deleted.
    reversed_at: Mapped[datetime | None]


class Wallet(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """What MUHUZE owes one seller. Its balances change ONLY through
    WalletTransactions and always equal their sum."""

    __tablename__ = "wallets"
    __table_args__ = (
        CheckConstraint(
            "pending_balance >= 0 AND available_balance >= 0"
            " AND total_earned >= 0 AND total_withdrawn >= 0",
            name="balances_not_negative",
        ),
    )

    seller_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sellers.id", ondelete="RESTRICT"), unique=True
    )
    currency: Mapped[str] = mapped_column(
        String(3), default=DEFAULT_CURRENCY, server_default=DEFAULT_CURRENCY
    )
    # Earned, but the buyer has not confirmed receipt: cannot be withdrawn.
    pending_balance: Mapped[Decimal] = mapped_column(Money, default=Decimal(0), server_default="0")
    available_balance: Mapped[Decimal] = mapped_column(
        Money, default=Decimal(0), server_default="0"
    )
    total_earned: Mapped[Decimal] = mapped_column(Money, default=Decimal(0), server_default="0")
    total_withdrawn: Mapped[Decimal] = mapped_column(Money, default=Decimal(0), server_default="0")


class WalletTransaction(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """One movement in a wallet. Append-only."""

    __tablename__ = "wallet_transactions"
    __table_args__ = (
        # A sale is credited once, settled once, and reversed at most once,
        # whatever the application does (README §14, invariant 3).
        UniqueConstraint("revenue_transaction_id", "kind"),
        CheckConstraint(
            f"kind IN ({', '.join(repr(k.value) for k in WalletTransactionKind)})",
            name="kind_valid",
        ),
        Index("ix_wallet_transactions_wallet_id_created_at", "wallet_id", "created_at"),
    )

    wallet_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("wallets.id", ondelete="RESTRICT"))
    kind: Mapped[str] = mapped_column(String(20))
    pending_change: Mapped[Decimal] = mapped_column(Money)
    available_change: Mapped[Decimal] = mapped_column(Money)
    pending_after: Mapped[Decimal] = mapped_column(Money)
    available_after: Mapped[Decimal] = mapped_column(Money)
    revenue_transaction_id: Mapped[uuid.UUID] = mapped_column(
        # Named by hand: the conventional name is over PostgreSQL's
        # 63-character limit.
        ForeignKey(
            "revenue_transactions.id",
            ondelete="RESTRICT",
            name="fk_wallet_transactions_revenue_transaction_id",
        )
    )
