"""Persistence models for seller plans, subscriptions, and the default
commission rate.

Mirrors `docs/database/database_schema.dbml`; change both together.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, String, column, text
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.modules.seller_plans.seller_plan_constants import (
    DEFAULT_CURRENCY,
    NOTE_MAX_LENGTH,
    PAYMENT_REFERENCE_MAX_LENGTH,
    PLAN_DESCRIPTION_MAX_LENGTH,
    PLAN_NAME_MAX_LENGTH,
    PRICE_DECIMAL_PLACES,
    PRICE_MAX_DIGITS,
    RATE_DECIMAL_PLACES,
    RATE_MAX_DIGITS,
    STATUS_REASON_MAX_LENGTH,
    PlanStatus,
    SubscriptionStatus,
)

Money = Numeric(PRICE_MAX_DIGITS, PRICE_DECIMAL_PLACES)
Rate = Numeric(RATE_MAX_DIGITS, RATE_DECIMAL_PLACES)
RATE_IN_RANGE = "{column} >= 0 AND {column} <= 100"


def _in_values(column_name: str, enum: type[StrEnum]) -> str:
    return f"{column_name} IN ({', '.join(repr(member.value) for member in enum)})"


class SellerPlan(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A plan admins offer to sellers. Never deleted once a subscription uses
    it; it is retired instead."""

    __tablename__ = "seller_plans"
    __table_args__ = (
        CheckConstraint("price >= 0", name="price_not_negative"),
        CheckConstraint("duration_days > 0", name="duration_positive"),
        CheckConstraint(
            RATE_IN_RANGE.format(column="commission_rate"), name="commission_rate_in_range"
        ),
        CheckConstraint(_in_values("status", PlanStatus), name="status_valid"),
    )

    code: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(PLAN_NAME_MAX_LENGTH))
    description: Mapped[str | None] = mapped_column(String(PLAN_DESCRIPTION_MAX_LENGTH))
    price: Mapped[Decimal] = mapped_column(Money)
    currency: Mapped[str] = mapped_column(
        String(3), default=DEFAULT_CURRENCY, server_default=DEFAULT_CURRENCY
    )
    duration_days: Mapped[int]
    commission_rate: Mapped[Decimal] = mapped_column(Rate)
    status: Mapped[str] = mapped_column(
        String(20), default=PlanStatus.ACTIVE.value, server_default=PlanStatus.ACTIVE.value
    )
    created_by_account_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("accounts.id", ondelete="SET NULL")
    )


class SellerSubscription(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A seller's plan for one period. A seller has a history of these.

    Applicable at a moment = status `active` AND starts_at <= moment < ends_at.
    The plan_name / price / … columns are a snapshot of the plan when the
    subscription was requested: they are what applies, whatever the plan
    says now.
    """

    __tablename__ = "seller_subscriptions"
    __table_args__ = (
        # The guarantee behind "at most one applicable subscription per
        # seller at any moment" (README §10.2): two ACTIVE subscriptions of
        # one seller can never have overlapping periods. Needs btree_gist.
        ExcludeConstraint(
            (column("seller_id"), "="),
            (text("tstzrange(starts_at, ends_at)"), "&&"),
            where=text("status = 'active'"),
            using="gist",
            name="ex_seller_subscriptions_active_periods_no_overlap",
        ),
        # One open request per seller.
        Index(
            "uq_seller_subscriptions_seller_id_pending",
            "seller_id",
            unique=True,
            postgresql_where=text("status = 'pending'"),
        ),
        Index("ix_seller_subscriptions_seller_id_status", "seller_id", "status"),
        CheckConstraint(_in_values("status", SubscriptionStatus), name="status_valid"),
        CheckConstraint("ends_at > starts_at", name="period_valid"),
        CheckConstraint(
            "status <> 'active' OR (starts_at IS NOT NULL AND ends_at IS NOT NULL)",
            name="active_has_period",
        ),
    )

    seller_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sellers.id", ondelete="RESTRICT"))
    plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("seller_plans.id", ondelete="RESTRICT"))
    status: Mapped[str] = mapped_column(
        String(20),
        default=SubscriptionStatus.PENDING.value,
        server_default=SubscriptionStatus.PENDING.value,
    )

    plan_name: Mapped[str] = mapped_column(String(PLAN_NAME_MAX_LENGTH))
    price: Mapped[Decimal] = mapped_column(Money)
    currency: Mapped[str] = mapped_column(String(3))
    duration_days: Mapped[int]
    commission_rate: Mapped[Decimal] = mapped_column(Rate)

    starts_at: Mapped[datetime | None]
    ends_at: Mapped[datetime | None]

    requested_by_account_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("accounts.id", ondelete="SET NULL")
    )
    decided_by_account_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("accounts.id", ondelete="SET NULL")
    )
    decided_at: Mapped[datetime | None]
    ended_by_account_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("accounts.id", ondelete="SET NULL")
    )
    status_reason: Mapped[str | None] = mapped_column(String(STATUS_REASON_MAX_LENGTH))
    # What the admin checked before activating (a MoMo or bank reference).
    # Becomes a link to the payment record when the payments feature exists.
    payment_reference: Mapped[str | None] = mapped_column(String(PAYMENT_REFERENCE_MAX_LENGTH))


class DefaultCommissionRate(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """MUHUZE's rate for sellers with no applicable subscription.

    Effective-dated and append-only: a change is a new row. The current rate
    is the row with the latest effective_from that is not in the future.
    """

    __tablename__ = "default_commission_rates"
    __table_args__ = (CheckConstraint(RATE_IN_RANGE.format(column="rate"), name="rate_in_range"),)

    rate: Mapped[Decimal] = mapped_column(Rate)
    effective_from: Mapped[datetime] = mapped_column(unique=True)
    note: Mapped[str | None] = mapped_column(String(NOTE_MAX_LENGTH))
    set_by_account_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("accounts.id", ondelete="SET NULL")
    )
