import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDPKMixin


class RevenueTransaction(UUIDPKMixin, TimestampMixin, Base):
    """The single accounting record — MUHUZE's revenue for a sale, and the
    seller's net earning, derived **exactly once** in the same DB transaction
    as `Payment → paid`.

    There is one row per (order, seller): each seller in a multi-seller order
    is charged their own commission rate (7% premium / 12% basic), so the
    split has to be per seller, not per order total.

    `revenue_rate` is a *snapshot* taken from the seller's active premium
    subscription (or the 12% basic baseline) at `paid` time — so the rate
    actually applied stays auditable forever even if the subscription later
    changes.

    `order_id` + `seller_id` is unique, giving the idempotency guard: a
    re-fired `paid` event must never double-credit a seller.

    **Escrow model:** when money lands on MUHUZE's account at `paid`,
    `commission_amount` is MUHUZE's to keep straight away, while the
    `seller_earning` is *held* (`status = held`) — the money MUHUZE will send
    the seller only once the buyer confirms receipt. `OrderService.receive`
    flips it to `released` and stamps `released_at`.
    """

    __tablename__ = "revenue_transactions"
    __table_args__ = (
        UniqueConstraint(
            "order_id",
            "seller_id",
            name="uq_revenue_transactions_order_seller",
        ),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id"),
        nullable=False,
        index=True,
    )
    payment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payments.id"),
        nullable=False,
        index=True,
    )
    seller_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sellers.id"),
        nullable=False,
        index=True,
    )
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    revenue_rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    commission_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    seller_earning: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="RWF")
    referral_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="held", index=True
    )
    released_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return (
            f"<RevenueTransaction order={self.order_id} seller={self.seller_id} "
            f"rate={self.revenue_rate}% commission={self.commission_amount} "
            f"status={self.status}>"
        )
