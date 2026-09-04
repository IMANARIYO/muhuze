import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDPKMixin


class PaymentStatus(StrEnum):
    """Lifecycle of a single payment.

    `pending` → the payment intent exists but money hasn't cleared.
    `awaiting` → the buyer reported that they sent the money outside the app
    (MoMo USSD/app); MUHUZE has not yet verified receipt. No revenue is
    derived yet and no seller orders are opened at this point.
    `paid` → MUHUZE admin confirmed the money actually arrived. This is the
    exact moment the commission split is derived into `revenue_transactions`
    and the sellers' `seller_order`s are opened.
    `failed` → the payment attempt failed; the order remains unpaid.
    `refunded` / `partially_refunded` → reversal states (Phase 2 engines).
    """

    PENDING = "pending"
    AWAITING = "awaiting"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class Payment(UUIDPKMixin, TimestampMixin, Base):
    """One payment for one order.

    Kept in its own module (not tangled into orders) so money-in logic stays
    cleanly separated from order/fulfillment concerns. v1 uses **mobile money
    (Airtel Money)** captured via a stub gateway:

    * `momo_phone`   — the buyer's Airtel Money wallet to charge.
    * `airtel_phone` — the registered Airtel line the payment is sent from /
      MO:MUHUZE receives the USSD request (kept for the real PSP swap-in).
    * `request_reference` — the gateway's id, stored in `provider_ref`.

    The pipeline is `create` (request-payment -> `pending`, reference stored)
    then the provider callback (`/paid`) clears the money, which is the exact
    moment revenue is derived. `method` / `provider_ref` stay compatible with
    a future PSP.
    """

    __tablename__ = "payments"

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=PaymentStatus.PENDING, index=True
    )
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="RWF")
    momo_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    airtel_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    method: Mapped[str | None] = mapped_column(String(30), nullable=True)
    provider_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<Payment order={self.order_id} {self.status} {self.amount}>"
