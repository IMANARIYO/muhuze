"""create revenue and wallet tables

Revision ID: 0009
Revises: 0008
Create Date: 2026-10-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MONEY = sa.Numeric(precision=14, scale=2)


def _timestamp(name: str) -> sa.Column:
    return sa.Column(name, sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)


def upgrade() -> None:
    op.create_table(
        "revenue_transactions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("seller_order_id", sa.Uuid(), nullable=False),
        sa.Column("order_id", sa.Uuid(), nullable=False),
        sa.Column("seller_id", sa.Uuid(), nullable=False),
        sa.Column("gross_amount", MONEY, nullable=False),
        sa.Column("commission_rate", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("commission_amount", MONEY, nullable=False),
        sa.Column("seller_amount", MONEY, nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("reversed_at", sa.DateTime(timezone=True), nullable=True),
        _timestamp("created_at"),
        sa.PrimaryKeyConstraint("id", name="pk_revenue_transactions"),
        sa.ForeignKeyConstraint(
            ["seller_order_id"],
            ["seller_orders.id"],
            name="fk_revenue_transactions_seller_order_id_seller_orders",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"],
            name="fk_revenue_transactions_order_id_orders",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["seller_id"],
            ["sellers.id"],
            name="fk_revenue_transactions_seller_id_sellers",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("seller_order_id", name="uq_revenue_transactions_seller_order_id"),
        sa.CheckConstraint(
            "gross_amount >= 0 AND commission_amount >= 0 AND seller_amount >= 0",
            name=op.f("ck_revenue_transactions_amounts_not_negative"),
        ),
        sa.CheckConstraint(
            "commission_amount + seller_amount = gross_amount",
            name=op.f("ck_revenue_transactions_split_adds_up"),
        ),
    )
    op.create_index("ix_revenue_transactions_order_id", "revenue_transactions", ["order_id"])
    op.create_index("ix_revenue_transactions_seller_id", "revenue_transactions", ["seller_id"])

    op.create_table(
        "wallets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("seller_id", sa.Uuid(), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="RWF", nullable=False),
        sa.Column("pending_balance", MONEY, server_default="0", nullable=False),
        sa.Column("available_balance", MONEY, server_default="0", nullable=False),
        sa.Column("total_earned", MONEY, server_default="0", nullable=False),
        sa.Column("total_withdrawn", MONEY, server_default="0", nullable=False),
        _timestamp("created_at"),
        _timestamp("updated_at"),
        sa.PrimaryKeyConstraint("id", name="pk_wallets"),
        sa.ForeignKeyConstraint(
            ["seller_id"], ["sellers.id"], name="fk_wallets_seller_id_sellers", ondelete="RESTRICT"
        ),
        sa.UniqueConstraint("seller_id", name="uq_wallets_seller_id"),
        sa.CheckConstraint(
            "pending_balance >= 0 AND available_balance >= 0"
            " AND total_earned >= 0 AND total_withdrawn >= 0",
            name=op.f("ck_wallets_balances_not_negative"),
        ),
    )

    op.create_table(
        "wallet_transactions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("wallet_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("pending_change", MONEY, nullable=False),
        sa.Column("available_change", MONEY, nullable=False),
        sa.Column("pending_after", MONEY, nullable=False),
        sa.Column("available_after", MONEY, nullable=False),
        sa.Column("revenue_transaction_id", sa.Uuid(), nullable=False),
        _timestamp("created_at"),
        sa.PrimaryKeyConstraint("id", name="pk_wallet_transactions"),
        sa.ForeignKeyConstraint(
            ["wallet_id"],
            ["wallets.id"],
            name="fk_wallet_transactions_wallet_id_wallets",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["revenue_transaction_id"],
            ["revenue_transactions.id"],
            name="fk_wallet_transactions_revenue_transaction_id",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "revenue_transaction_id",
            "kind",
            name="uq_wallet_transactions_revenue_transaction_id_kind",
        ),
        sa.CheckConstraint(
            "kind IN ('earning', 'settlement', 'reversal')",
            name=op.f("ck_wallet_transactions_kind_valid"),
        ),
    )
    op.create_index(
        "ix_wallet_transactions_wallet_id_created_at",
        "wallet_transactions",
        ["wallet_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_table("wallet_transactions")
    op.drop_table("wallets")
    op.drop_table("revenue_transactions")
