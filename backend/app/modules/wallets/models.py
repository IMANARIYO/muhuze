import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDPKMixin


class WalletTransactionType(StrEnum):
    """What moved money in or out of a seller wallet.

    * `earnings`    — a seller's net earning from a paid order, credited when
      the payment clears (starts in the `held` bucket).
    * `release`     — freed from escrow when the buyer confirms receipt; moves
      money from `held` to `available`.
    * `withdrawal`  — a seller requested payout to their own mobile-money
      number; debits `available`.
    * `adjustment`  — manual platform-corrected movement (admin).
    """

    EARNINGS = "earnings"
    RELEASE = "release"
    WITHDRAWAL = "withdrawal"
    ADJUSTMENT = "adjustment"


class WalletTransactionStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WithdrawalStatus(StrEnum):
    """Lifecycle of a withdrawal request.

    `requested` → the seller asked to withdraw to their mobile-money number.
    `processing` → admin is issuing the payout (out-of-system MoMo transfer).
    `completed` → the money was sent; wallet debited permanently.
    `cancelled` → rejected/abandoned; nothing was debited.
    """

    REQUESTED = "requested"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Wallet(UUIDPKMixin, TimestampMixin, Base):
    """A single financial ledger per seller.

    There is exactly one wallet per seller (1:0..1). Rather than duplicating
    money facts, the balances are reconciled in the wallet service from the
    three canonical sources: `revenue_transactions` (earnings + releases),
    `withdrawal_requests` (money sent out), and manual adjustments recorded
    as wallet transactions. `available_balance` is what a seller can actually
    request to withdraw; `held_balance` is escrow awaiting buyer receipt.
    """

    __tablename__ = "wallets"

    seller_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        unique=True,
        nullable=False,
        index=True,
    )
    available_balance: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    held_balance: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    total_earned: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    total_withdrawn: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="RWF")

    def __repr__(self) -> str:
        return (
            f"<Wallet seller={self.seller_id} available={self.available_balance} "
            f"held={self.held_balance} withdrawn={self.total_withdrawn}>"
        )


class WalletTransaction(UUIDPKMixin, TimestampMixin, Base):
    """One ledger movement on a wallet.

    `amount` is signed: positive credits the wallet bucket it targets,
    negative debits it (withdrawals/adjustments). `balance_after` records the
    resulting `available_balance` for auditability. `reference_type`
    points back at the source fact (a revenue_transaction, an order, or a
    withdrawal) so every row is provable from the underlying money event.
    """

    __tablename__ = "wallet_transactions"
    __table_args__ = (
        UniqueConstraint(
            "reference_type",
            "reference_id",
            name="uq_wallet_transactions_reference",
        ),
    )

    wallet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    type: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    balance_after: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="RWF")
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=WalletTransactionStatus.COMPLETED
    )
    reference_type: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    reference_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<WalletTransaction wallet={self.wallet_id} {self.type} {self.amount}>"


class WithdrawalRequest(UUIDPKMixin, TimestampMixin, Base):
    """A seller's request to move `available_balance` out of their wallet via
    mobile money.

    The payout itself happens **outside** the system (admin sends MoMo to the
    seller's `mobile_money_number`). The admin drives this row through
    `requested -> processing -> completed` (or `cancelled`), and it is at
    `completed` that the wallet is actually debited — so the balance is only
    reduced when the money really left MUHUZE's side.
    """

    __tablename__ = "withdrawal_requests"

    wallet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    seller_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="RWF")
    mobile_money_number: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=WithdrawalStatus.REQUESTED, index=True
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    processed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<WithdrawalRequest seller={self.seller_id} {self.amount} {self.status}>"
