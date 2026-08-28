import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDPKMixin


class SubscriptionStatus(StrEnum):
    """Lifecycle of a single seller subscription record.

    `active` — currently in effect (the row whose `expires_at` is still in
    the future and that wasn't cancelled). `expired` — its term has ended
    (either naturally or because the seller bought a new plan, which closes
    out the prior `active` row). `cancelled` — the seller actively cancelled
    before the term ended.
    """

    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class PremiumPlan(UUIDPKMixin, TimestampMixin, Base):
    """A purchasable premium tier. This is the config table for the rates:
    `commission_rate` is the percentage of every sale MUHUZE keeps *while a
    seller is on this plan* — 7% for premium vs. the 12% baseline paid by
    an unsubscribed (basic) seller. That difference is the whole point of a
    subscription set in this table, so it is loaded at order/commission
    time to decide the deduction.

    Reads are public (the "subscribe" page must show what's on offer);
    writes are admin-only to keep the catalogue of plans controlled.
    Plans aren't hard-deleted — `is_active=false` retires them without
    breaking the history that references them.
    """

    __tablename__ = "premium_plans"

    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    commission_rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    listing_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    premium_badge: Mapped[bool] = mapped_column(nullable=False, default=False)
    unlimited_listings: Mapped[bool] = mapped_column(nullable=False, default=False)
    priority_notifications: Mapped[bool] = mapped_column(nullable=False, default=False)
    early_promotion_access: Mapped[bool] = mapped_column(nullable=False, default=False)
    premium_only_promotions: Mapped[bool] = mapped_column(nullable=False, default=False)
    premium_discounts: Mapped[bool] = mapped_column(nullable=False, default=False)
    enhanced_favorites: Mapped[bool] = mapped_column(nullable=False, default=False)
    priority_support: Mapped[bool] = mapped_column(nullable=False, default=False)
    priority_service_handling: Mapped[bool] = mapped_column(nullable=False, default=False)
    referral_commission_eligible: Mapped[bool] = mapped_column(
        nullable=False, default=False
    )
    enhanced_visibility: Mapped[bool] = mapped_column(nullable=False, default=False)
    promotional_advantages: Mapped[bool] = mapped_column(nullable=False, default=False)
    advanced_analytics: Mapped[bool] = mapped_column(nullable=False, default=False)
    seller_verification_eligible: Mapped[bool] = mapped_column(
        nullable=False, default=False
    )
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)

    def __repr__(self) -> str:
        return f"<PremiumPlan {self.code} ({self.price} {self.currency}/{self.duration_days}d)>"


class SellerSubscription(UUIDPKMixin, TimestampMixin, Base):
    """One seller's purchase of a premium plan. A seller can hold many rows —
    this is full purchase history, never overwritten. At most one row should
    be `active` for a given seller at a time; buying a new plan closes out
    (marks `expired`) the previous `active` one.

    `commission_rate` is a *snapshot* of the plan's rate at purchase time,
    so the rate that applies to the seller's sales stays auditable even if
    the plan's `commission_rate` is later edited. Do the commission
    deduction against the active subscription's snapshot — never by
    re-reading the plan at sale time.
    """

    __tablename__ = "seller_subscriptions"

    seller_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sellers.id"),
        nullable=False,
        index=True,
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("premium_plans.id"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=SubscriptionStatus.ACTIVE, index=True
    )
    commission_rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return (
            f"<SellerSubscription seller={self.seller_id} "
            f"{self.status} {self.starts_at:%Y-%m-%d}->{self.expires_at:%Y-%m-%d}>"
        )
