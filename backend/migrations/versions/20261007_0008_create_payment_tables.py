"""create payment tables

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamp(name: str) -> sa.Column:
    return sa.Column(name, sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)


def _account(table: str, column: str, ondelete: str) -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint(
        [column], ["accounts.id"], name=f"fk_{table}_{column}_accounts", ondelete=ondelete
    )


def upgrade() -> None:
    op.create_table(
        "payment_destinations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("method", sa.String(length=20), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("account_reference", sa.String(length=100), nullable=False),
        sa.Column("registered_name", sa.String(length=150), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="RWF", nullable=False),
        sa.Column("instructions", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("is_default", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_by_account_id", sa.Uuid(), nullable=True),
        _timestamp("created_at"),
        _timestamp("updated_at"),
        sa.PrimaryKeyConstraint("id", name="pk_payment_destinations"),
        _account("payment_destinations", "created_by_account_id", "SET NULL"),
        sa.CheckConstraint(
            "method IN ('mobile_money', 'merchant_code', 'bank_transfer')",
            name=op.f("ck_payment_destinations_method_valid"),
        ),
        sa.CheckConstraint(
            "NOT is_default OR is_active", name=op.f("ck_payment_destinations_default_is_active")
        ),
    )
    op.create_index(
        "uq_payment_destinations_currency_default",
        "payment_destinations",
        ["currency"],
        unique=True,
        postgresql_where=sa.text("is_default"),
    )

    op.create_table(
        "payments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("purpose", sa.String(length=20), server_default="order", nullable=False),
        sa.Column("order_id", sa.Uuid(), nullable=False),
        sa.Column("order_number", sa.String(length=20), nullable=False),
        sa.Column("payer_account_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("channel", sa.String(length=20), server_default="manual", nullable=False),
        sa.Column(
            "status", sa.String(length=30), server_default="awaiting_verification", nullable=False
        ),
        sa.Column("destination_id", sa.Uuid(), nullable=False),
        sa.Column("destination_method", sa.String(length=20), nullable=False),
        sa.Column("destination_provider", sa.String(length=100), nullable=False),
        sa.Column("destination_account_reference", sa.String(length=100), nullable=False),
        sa.Column("destination_registered_name", sa.String(length=150), nullable=False),
        sa.Column("reference", sa.String(length=100), nullable=False),
        sa.Column("payer_name", sa.String(length=150), nullable=True),
        sa.Column("payer_phone", sa.String(length=20), nullable=True),
        sa.Column("verified_by_account_id", sa.Uuid(), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.String(length=500), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        _timestamp("created_at"),
        _timestamp("updated_at"),
        sa.PrimaryKeyConstraint("id", name="pk_payments"),
        sa.ForeignKeyConstraint(
            ["order_id"], ["orders.id"], name="fk_payments_order_id_orders", ondelete="RESTRICT"
        ),
        _account("payments", "payer_account_id", "RESTRICT"),
        sa.ForeignKeyConstraint(
            ["destination_id"],
            ["payment_destinations.id"],
            name="fk_payments_destination_id_payment_destinations",
            ondelete="RESTRICT",
        ),
        _account("payments", "verified_by_account_id", "SET NULL"),
        sa.CheckConstraint(
            "status IN ('awaiting_verification', 'paid', 'rejected')",
            name=op.f("ck_payments_status_valid"),
        ),
        sa.CheckConstraint("purpose IN ('order')", name=op.f("ck_payments_purpose_valid")),
        sa.CheckConstraint("channel IN ('manual')", name=op.f("ck_payments_channel_valid")),
        sa.CheckConstraint("amount > 0", name=op.f("ck_payments_amount_positive")),
    )
    op.create_index(
        "uq_payments_order_id_paid",
        "payments",
        ["order_id"],
        unique=True,
        postgresql_where=sa.text("status = 'paid'"),
    )
    op.create_index(
        "uq_payments_order_id_awaiting_verification",
        "payments",
        ["order_id"],
        unique=True,
        postgresql_where=sa.text("status = 'awaiting_verification'"),
    )
    op.create_index(
        "uq_payments_reference_lower",
        "payments",
        [sa.text("lower(reference)")],
        unique=True,
        postgresql_where=sa.text("status <> 'rejected'"),
    )
    op.create_index("ix_payments_status_created_at", "payments", ["status", "created_at"])
    op.create_index("ix_payments_order_id", "payments", ["order_id"])


def downgrade() -> None:
    op.drop_table("payments")
    op.drop_table("payment_destinations")
