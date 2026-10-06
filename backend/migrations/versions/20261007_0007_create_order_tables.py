"""create order tables

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MONEY = sa.Numeric(precision=14, scale=2)


def _timestamp(name: str) -> sa.Column:
    return sa.Column(name, sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)


def upgrade() -> None:
    # Order numbers (MHZ-000123) come from this sequence.
    op.execute(sa.schema.CreateSequence(sa.Sequence("order_number_seq")))

    op.create_table(
        "orders",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("order_number", sa.String(length=20), nullable=False),
        sa.Column("buyer_account_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status", sa.String(length=20), server_default="awaiting_payment", nullable=False
        ),
        sa.Column("currency", sa.String(length=3), server_default="RWF", nullable=False),
        sa.Column("total_amount", MONEY, nullable=False),
        sa.Column("recipient_name", sa.String(length=150), nullable=False),
        sa.Column("recipient_phone", sa.String(length=20), nullable=False),
        sa.Column("delivery_province", sa.String(length=100), nullable=False),
        sa.Column("delivery_district", sa.String(length=100), nullable=False),
        sa.Column("delivery_sector", sa.String(length=100), nullable=False),
        sa.Column("delivery_address", sa.String(length=255), nullable=True),
        sa.Column("buyer_note", sa.String(length=500), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_reason", sa.String(length=500), nullable=True),
        _timestamp("created_at"),
        _timestamp("updated_at"),
        sa.PrimaryKeyConstraint("id", name="pk_orders"),
        sa.ForeignKeyConstraint(
            ["buyer_account_id"],
            ["accounts.id"],
            name="fk_orders_buyer_account_id_accounts",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("order_number", name="uq_orders_order_number"),
        sa.CheckConstraint(
            "status IN ('awaiting_payment', 'in_progress', 'completed', 'cancelled')",
            name=op.f("ck_orders_status_valid"),
        ),
        sa.CheckConstraint("total_amount >= 0", name=op.f("ck_orders_total_not_negative")),
    )
    op.create_index(
        "ix_orders_buyer_account_id_created_at", "orders", ["buyer_account_id", "created_at"]
    )

    op.create_table(
        "seller_orders",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("order_id", sa.Uuid(), nullable=False),
        sa.Column("seller_id", sa.Uuid(), nullable=False),
        sa.Column("seller_name", sa.String(length=150), nullable=False),
        sa.Column(
            "status", sa.String(length=20), server_default="awaiting_payment", nullable=False
        ),
        sa.Column("status_reason", sa.String(length=500), nullable=True),
        sa.Column("subtotal", MONEY, nullable=False),
        sa.Column("commission_rate", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("commission_amount", MONEY, nullable=False),
        sa.Column("seller_amount", MONEY, nullable=False),
        sa.Column("terms_source", sa.String(length=20), nullable=False),
        sa.Column("subscription_id", sa.Uuid(), nullable=True),
        sa.Column("plan_name", sa.String(length=100), nullable=True),
        sa.Column("default_rate_id", sa.Uuid(), nullable=True),
        _timestamp("created_at"),
        _timestamp("updated_at"),
        sa.PrimaryKeyConstraint("id", name="pk_seller_orders"),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"],
            name="fk_seller_orders_order_id_orders",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["seller_id"],
            ["sellers.id"],
            name="fk_seller_orders_seller_id_sellers",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["subscription_id"],
            ["seller_subscriptions.id"],
            name="fk_seller_orders_subscription_id_seller_subscriptions",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["default_rate_id"],
            ["default_commission_rates.id"],
            name="fk_seller_orders_default_rate_id_default_commission_rates",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("order_id", "seller_id", name="uq_seller_orders_order_id_seller_id"),
        sa.CheckConstraint(
            "status IN ('awaiting_payment', 'pending', 'accepted', 'shipped', 'delivered',"
            " 'completed', 'rejected', 'cancelled')",
            name=op.f("ck_seller_orders_status_valid"),
        ),
        sa.CheckConstraint(
            "subtotal >= 0 AND commission_amount >= 0 AND seller_amount >= 0",
            name=op.f("ck_seller_orders_amounts_not_negative"),
        ),
        sa.CheckConstraint(
            "commission_amount + seller_amount = subtotal",
            name=op.f("ck_seller_orders_split_adds_up"),
        ),
        sa.CheckConstraint(
            "(terms_source = 'subscription' AND subscription_id IS NOT NULL"
            " AND default_rate_id IS NULL)"
            " OR (terms_source = 'default' AND default_rate_id IS NOT NULL"
            " AND subscription_id IS NULL)",
            name=op.f("ck_seller_orders_terms_source_recorded"),
        ),
    )
    op.create_index(
        "ix_seller_orders_seller_id_status_created_at",
        "seller_orders",
        ["seller_id", "status", "created_at"],
    )

    op.create_table(
        "order_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("seller_order_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("product_name", sa.String(length=200), nullable=False),
        sa.Column("unit_price", MONEY, nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("line_total", MONEY, nullable=False),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("attributes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        _timestamp("created_at"),
        sa.PrimaryKeyConstraint("id", name="pk_order_items"),
        sa.ForeignKeyConstraint(
            ["seller_order_id"],
            ["seller_orders.id"],
            name="fk_order_items_seller_order_id_seller_orders",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name="fk_order_items_product_id_products",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "seller_order_id", "product_id", name="uq_order_items_seller_order_id_product_id"
        ),
        sa.CheckConstraint("quantity > 0", name=op.f("ck_order_items_quantity_positive")),
        sa.CheckConstraint(
            "line_total = unit_price * quantity", name=op.f("ck_order_items_line_total_correct")
        ),
    )
    op.create_index("ix_order_items_seller_order_id", "order_items", ["seller_order_id"])

    op.create_table(
        "seller_order_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("seller_order_id", sa.Uuid(), nullable=False),
        sa.Column("from_status", sa.String(length=20), nullable=True),
        sa.Column("to_status", sa.String(length=20), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=True),
        sa.Column("actor_account_id", sa.Uuid(), nullable=True),
        _timestamp("created_at"),
        sa.PrimaryKeyConstraint("id", name="pk_seller_order_events"),
        sa.ForeignKeyConstraint(
            ["seller_order_id"],
            ["seller_orders.id"],
            name="fk_seller_order_events_seller_order_id_seller_orders",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["actor_account_id"],
            ["accounts.id"],
            name="fk_seller_order_events_actor_account_id_accounts",
            ondelete="SET NULL",
        ),
    )
    op.create_index(
        "ix_seller_order_events_seller_order_id", "seller_order_events", ["seller_order_id"]
    )


def downgrade() -> None:
    op.drop_table("seller_order_events")
    op.drop_table("order_items")
    op.drop_table("seller_orders")
    op.drop_table("orders")
    op.execute(sa.schema.DropSequence(sa.Sequence("order_number_seq")))
