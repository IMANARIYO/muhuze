"""create withdrawal tables and link wallet movements to withdrawals

Revision ID: 0010
Revises: 0009
Create Date: 2026-10-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MONEY = sa.Numeric(precision=14, scale=2)

KINDS = (
    "'earning', 'settlement', 'reversal', 'withdrawal', 'withdrawal_release', 'withdrawal_complete'"
)


def _timestamp(name: str) -> sa.Column:
    return sa.Column(name, sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)


def upgrade() -> None:
    op.create_table(
        "seller_payout_destinations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("seller_id", sa.Uuid(), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("account_number", sa.String(length=100), nullable=False),
        sa.Column("account_name", sa.String(length=150), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        _timestamp("created_at"),
        _timestamp("updated_at"),
        sa.PrimaryKeyConstraint("id", name="pk_seller_payout_destinations"),
        sa.ForeignKeyConstraint(
            ["seller_id"],
            ["sellers.id"],
            name="fk_seller_payout_destinations_seller_id_sellers",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "type IN ('mobile_money', 'bank')",
            name=op.f("ck_seller_payout_destinations_type_valid"),
        ),
    )
    op.create_index(
        "ix_seller_payout_destinations_seller_id",
        "seller_payout_destinations",
        ["seller_id"],
    )

    op.create_table(
        "withdrawals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("seller_id", sa.Uuid(), nullable=False),
        sa.Column("payout_destination_id", sa.Uuid(), nullable=False),
        sa.Column("amount", MONEY, nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="RWF", nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("destination_type", sa.String(length=20), nullable=False),
        sa.Column("destination_provider", sa.String(length=100), nullable=False),
        sa.Column("destination_account_number", sa.String(length=100), nullable=False),
        sa.Column("destination_account_name", sa.String(length=150), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=True),
        sa.Column("payout_reference", sa.String(length=100), nullable=True),
        sa.Column("reviewed_by_account_id", sa.Uuid(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        _timestamp("created_at"),
        _timestamp("updated_at"),
        sa.PrimaryKeyConstraint("id", name="pk_withdrawals"),
        sa.ForeignKeyConstraint(
            ["seller_id"],
            ["sellers.id"],
            name="fk_withdrawals_seller_id_sellers",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["payout_destination_id"],
            ["seller_payout_destinations.id"],
            name="fk_withdrawals_payout_destination_id_seller_payout_destinations",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by_account_id"],
            ["accounts.id"],
            name="fk_withdrawals_reviewed_by_account_id_accounts",
            ondelete="SET NULL",
        ),
        sa.Index("ix_withdrawals_seller_id", "seller_id"),
        sa.Index("ix_withdrawals_status_created_at", "status", "created_at"),
        sa.CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'rejected', 'failed', 'cancelled')",
            name=op.f("ck_withdrawals_status_valid"),
        ),
        sa.CheckConstraint("amount > 0", name=op.f("ck_withdrawals_amount_positive")),
    )

    # The ledger grows a second possible source: a withdrawal instead of a
    # sale. Exactly one of the two is set.
    op.add_column(
        "wallet_transactions",
        sa.Column("withdrawal_id", sa.Uuid(), nullable=True),
    )
    op.alter_column(
        "wallet_transactions",
        "revenue_transaction_id",
        existing_type=sa.Uuid(),
        nullable=True,
    )
    op.create_foreign_key(
        "fk_wallet_transactions_withdrawal_id_withdrawals",
        "wallet_transactions",
        "withdrawals",
        ["withdrawal_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_unique_constraint(
        "uq_wallet_transactions_withdrawal_id_kind",
        "wallet_transactions",
        ["withdrawal_id", "kind"],
    )
    op.drop_constraint(
        op.f("ck_wallet_transactions_kind_valid"), "wallet_transactions", type_="check"
    )
    op.create_check_constraint(
        op.f("ck_wallet_transactions_kind_valid"),
        "wallet_transactions",
        f"kind IN ({KINDS})",
    )
    op.create_check_constraint(
        op.f("ck_wallet_transactions_one_source"),
        "wallet_transactions",
        "(revenue_transaction_id IS NULL) <> (withdrawal_id IS NULL)",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("ck_wallet_transactions_one_source"), "wallet_transactions", type_="check"
    )
    op.drop_constraint(
        op.f("ck_wallet_transactions_kind_valid"), "wallet_transactions", type_="check"
    )
    op.create_check_constraint(
        op.f("ck_wallet_transactions_kind_valid"),
        "wallet_transactions",
        "kind IN ('earning', 'settlement', 'reversal')",
    )
    op.drop_constraint(
        "uq_wallet_transactions_withdrawal_id_kind", "wallet_transactions", type_="unique"
    )
    op.drop_constraint(
        "fk_wallet_transactions_withdrawal_id_withdrawals",
        "wallet_transactions",
        type_="foreignkey",
    )
    op.alter_column(
        "wallet_transactions",
        "revenue_transaction_id",
        existing_type=sa.Uuid(),
        nullable=False,
    )
    op.drop_column("wallet_transactions", "withdrawal_id")
    op.drop_table("withdrawals")
    op.drop_table("seller_payout_destinations")
