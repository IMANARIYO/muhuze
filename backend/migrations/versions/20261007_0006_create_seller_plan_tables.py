"""create seller plan tables

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamp(name: str) -> sa.Column:
    return sa.Column(name, sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)


def _account_reference(table: str, column: str) -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint(
        [column], ["accounts.id"], name=f"fk_{table}_{column}_accounts", ondelete="SET NULL"
    )


def upgrade() -> None:
    # Lets an exclusion constraint combine "same seller" (=) with
    # "overlapping period" (&&). Ships with PostgreSQL.
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")

    op.create_table(
        "seller_plans",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.Column("price", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="RWF", nullable=False),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("commission_rate", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
        sa.Column("created_by_account_id", sa.Uuid(), nullable=True),
        _timestamp("created_at"),
        _timestamp("updated_at"),
        sa.PrimaryKeyConstraint("id", name="pk_seller_plans"),
        _account_reference("seller_plans", "created_by_account_id"),
        sa.UniqueConstraint("code", name="uq_seller_plans_code"),
        sa.CheckConstraint("price >= 0", name=op.f("ck_seller_plans_price_not_negative")),
        sa.CheckConstraint("duration_days > 0", name=op.f("ck_seller_plans_duration_positive")),
        sa.CheckConstraint(
            "commission_rate >= 0 AND commission_rate <= 100",
            name=op.f("ck_seller_plans_commission_rate_in_range"),
        ),
        sa.CheckConstraint(
            "status IN ('active', 'retired')", name=op.f("ck_seller_plans_status_valid")
        ),
    )

    op.create_table(
        "seller_subscriptions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("seller_id", sa.Uuid(), nullable=False),
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("plan_name", sa.String(length=100), nullable=False),
        sa.Column("price", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("commission_rate", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("requested_by_account_id", sa.Uuid(), nullable=True),
        sa.Column("decided_by_account_id", sa.Uuid(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_by_account_id", sa.Uuid(), nullable=True),
        sa.Column("status_reason", sa.String(length=500), nullable=True),
        sa.Column("payment_reference", sa.String(length=100), nullable=True),
        _timestamp("created_at"),
        _timestamp("updated_at"),
        sa.PrimaryKeyConstraint("id", name="pk_seller_subscriptions"),
        sa.ForeignKeyConstraint(
            ["seller_id"],
            ["sellers.id"],
            name="fk_seller_subscriptions_seller_id_sellers",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["seller_plans.id"],
            name="fk_seller_subscriptions_plan_id_seller_plans",
            ondelete="RESTRICT",
        ),
        _account_reference("seller_subscriptions", "requested_by_account_id"),
        _account_reference("seller_subscriptions", "decided_by_account_id"),
        _account_reference("seller_subscriptions", "ended_by_account_id"),
        # At most one applicable subscription per seller at any moment.
        postgresql.ExcludeConstraint(
            (sa.column("seller_id"), "="),
            (sa.text("tstzrange(starts_at, ends_at)"), "&&"),
            where=sa.text("status = 'active'"),
            using="gist",
            name="ex_seller_subscriptions_active_periods_no_overlap",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'active', 'rejected', 'cancelled')",
            name=op.f("ck_seller_subscriptions_status_valid"),
        ),
        sa.CheckConstraint(
            "ends_at > starts_at", name=op.f("ck_seller_subscriptions_period_valid")
        ),
        sa.CheckConstraint(
            "status <> 'active' OR (starts_at IS NOT NULL AND ends_at IS NOT NULL)",
            name=op.f("ck_seller_subscriptions_active_has_period"),
        ),
    )
    op.create_index(
        "uq_seller_subscriptions_seller_id_pending",
        "seller_subscriptions",
        ["seller_id"],
        unique=True,
        postgresql_where=sa.text("status = 'pending'"),
    )
    op.create_index(
        "ix_seller_subscriptions_seller_id_status", "seller_subscriptions", ["seller_id", "status"]
    )

    op.create_table(
        "default_commission_rates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("rate", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("set_by_account_id", sa.Uuid(), nullable=True),
        _timestamp("created_at"),
        sa.PrimaryKeyConstraint("id", name="pk_default_commission_rates"),
        _account_reference("default_commission_rates", "set_by_account_id"),
        sa.UniqueConstraint("effective_from", name="uq_default_commission_rates_effective_from"),
        sa.CheckConstraint(
            "rate >= 0 AND rate <= 100", name=op.f("ck_default_commission_rates_rate_in_range")
        ),
    )


def downgrade() -> None:
    op.drop_table("default_commission_rates")
    op.drop_table("seller_subscriptions")
    op.drop_table("seller_plans")
    # btree_gist is left installed: other objects in the database may rely on it.
