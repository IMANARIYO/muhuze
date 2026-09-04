"""add wallet tables

Revision ID: c4f1a9b2e7d6
Revises: a0c43911c8bd
Create Date: 2026-09-04 00:00:00.000000

Adds the seller wallet ledger and withdrawal support: `wallets` (one per
seller, reconciled balances), `wallet_transactions` (auditable ledger
movements, uniquely back-referenced to their source fact), and
`withdrawal_requests` (seller asks to move available balance out via MoMo,
admin drives it to completion which is when the wallet is actually debited).
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c4f1a9b2e7d6"
down_revision: str | Sequence[str] | None = "a0c43911c8bd"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "wallets",
        sa.Column("seller_id", sa.UUID(), nullable=False),
        sa.Column("available_balance", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("held_balance", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("total_earned", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("total_withdrawn", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_wallets_seller_id", "wallets", ["seller_id"], unique=True)

    op.create_table(
        "wallet_transactions",
        sa.Column("wallet_id", sa.UUID(), nullable=False),
        sa.Column("type", sa.String(length=24), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("balance_after", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("reference_type", sa.String(length=40), nullable=True),
        sa.Column("reference_id", sa.UUID(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("reference_type", "reference_id", name="uq_wallet_transactions_reference"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_wallet_transactions_wallet_id", "wallet_transactions", ["wallet_id"], unique=False)
    op.create_index("ix_wallet_transactions_type", "wallet_transactions", ["type"], unique=False)
    op.create_index("ix_wallet_transactions_reference_type", "wallet_transactions", ["reference_type"], unique=False)
    op.create_index("ix_wallet_transactions_reference_id", "wallet_transactions", ["reference_id"], unique=False)

    op.create_table(
        "withdrawal_requests",
        sa.Column("wallet_id", sa.UUID(), nullable=False),
        sa.Column("seller_id", sa.UUID(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("mobile_money_number", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("processed_by", sa.UUID(), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_withdrawal_requests_wallet_id", "withdrawal_requests", ["wallet_id"], unique=False)
    op.create_index("ix_withdrawal_requests_seller_id", "withdrawal_requests", ["seller_id"], unique=False)
    op.create_index("ix_withdrawal_requests_status", "withdrawal_requests", ["status"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_withdrawal_requests_status", table_name="withdrawal_requests")
    op.drop_index("ix_withdrawal_requests_seller_id", table_name="withdrawal_requests")
    op.drop_index("ix_withdrawal_requests_wallet_id", table_name="withdrawal_requests")
    op.drop_table("withdrawal_requests")

    op.drop_index("ix_wallet_transactions_reference_id", table_name="wallet_transactions")
    op.drop_index("ix_wallet_transactions_reference_type", table_name="wallet_transactions")
    op.drop_index("ix_wallet_transactions_type", table_name="wallet_transactions")
    op.drop_index("ix_wallet_transactions_wallet_id", table_name="wallet_transactions")
    op.drop_table("wallet_transactions")

    op.drop_index("ix_wallets_seller_id", table_name="wallets")
    op.drop_table("wallets")
