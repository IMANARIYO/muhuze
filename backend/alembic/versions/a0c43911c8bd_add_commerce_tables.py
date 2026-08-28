"""add commerce tables

Revision ID: a0c43911c8bd
Revises: a7f62ec3797d
Create Date: 2026-08-28 00:00:00.000000

Adds the Phase-1 commerce schema: cart, shipping addresses, orders (with
order_items + shipping_infos snapshots), payments (Airtel Money via a stub
gateway), the accounting revenue_transactions, and the seller-side
fulfillment tables seller_orders + shipments (created at payment time).

Note: `orders` and `shipping_infos` share a circular FK pair (orders holds
shipping_info_id; shipping_infos holds order_id). Both are modeled nullable,
and the constraints are added in two passes at the end to avoid a
create-table ordering deadlock.

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a0c43911c8bd"
down_revision: str | Sequence[str] | None = "a7f62ec3797d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _uuid() -> sa.Column:
    return sa.Column("id", sa.UUID(), nullable=False)


def _timestamps() -> list[sa.Column]:
    return [
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
    ]


def upgrade() -> None:
    """Upgrade schema."""
    # ── shipping_addresses (the customer's address book) ──────────────
    op.create_table(
        "shipping_addresses",
        sa.Column("account_id", sa.UUID(), nullable=False),
        sa.Column("label", sa.String(length=50), nullable=True),
        sa.Column("recipient_name", sa.String(length=150), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("country", sa.String(length=60), nullable=False),
        sa.Column("province", sa.String(length=100), nullable=True),
        sa.Column("district", sa.String(length=100), nullable=True),
        sa.Column("sector", sa.String(length=100), nullable=True),
        sa.Column("cell", sa.String(length=100), nullable=True),
        sa.Column("village", sa.String(length=100), nullable=True),
        sa.Column("address_line", sa.String(length=255), nullable=True),
        sa.Column("delivery_instructions", sa.String(length=255), nullable=True),
        sa.Column("latitude", sa.Numeric(precision=10, scale=7), nullable=True),
        sa.Column("longitude", sa.Numeric(precision=10, scale=7), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        *_timestamps(),
        _uuid(),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_shipping_addresses_account_id"),
        "shipping_addresses",
        ["account_id"],
        unique=False,
    )

    # ── cart_items (implicit cart keyed by account) ───────────────────
    op.create_table(
        "cart_items",
        sa.Column("account_id", sa.UUID(), nullable=False),
        sa.Column("listing_id", sa.UUID(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        *_timestamps(),
        _uuid(),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"]),
        sa.ForeignKeyConstraint(["listing_id"], ["seller_listings.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("account_id", "listing_id", name="uq_cart_items_account_listing"),
    )
    op.create_index(
        op.f("ix_cart_items_account_id"), "cart_items", ["account_id"], unique=False
    )
    op.create_index(
        op.f("ix_cart_items_listing_id"), "cart_items", ["listing_id"], unique=False
    )

    # ── shipping_infos (immutable per-order delivery snapshot) ────────
    # order_id FK to orders is added at the end (circular with orders).
    op.create_table(
        "shipping_infos",
        sa.Column("order_id", sa.UUID(), nullable=True),
        sa.Column("recipient_name", sa.String(length=150), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("country", sa.String(length=60), nullable=False),
        sa.Column("province", sa.String(length=100), nullable=True),
        sa.Column("district", sa.String(length=100), nullable=True),
        sa.Column("sector", sa.String(length=100), nullable=True),
        sa.Column("cell", sa.String(length=100), nullable=True),
        sa.Column("village", sa.String(length=100), nullable=True),
        sa.Column("address_line", sa.String(length=255), nullable=True),
        sa.Column("delivery_instructions", sa.String(length=255), nullable=True),
        sa.Column("latitude", sa.Numeric(precision=10, scale=7), nullable=True),
        sa.Column("longitude", sa.Numeric(precision=10, scale=7), nullable=True),
        *_timestamps(),
        _uuid(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_shipping_infos_order_id"), "shipping_infos", ["order_id"], unique=False
    )

    # ── orders (buyer-owned, multi-seller capable) ────────────────────
    # shipping_info_id FK is added at the end (circular with shipping_infos).
    op.create_table(
        "orders",
        sa.Column("order_number", sa.String(length=30), nullable=False),
        sa.Column("buyer_account_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("payment_status", sa.String(length=20), nullable=False),
        sa.Column("shipping_address_id", sa.UUID(), nullable=True),
        sa.Column("shipping_info_id", sa.UUID(), nullable=True),
        sa.Column("contact_phone", sa.String(length=20), nullable=True),
        sa.Column("subtotal", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("shipping_fee", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("discount_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("total_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("notes", sa.String(length=255), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        _uuid(),
        sa.ForeignKeyConstraint(["buyer_account_id"], ["accounts.id"]),
        sa.ForeignKeyConstraint(["shipping_address_id"], ["shipping_addresses.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_orders_order_number"), "orders", ["order_number"], unique=True
    )
    op.create_index(
        op.f("ix_orders_buyer_account_id"), "orders", ["buyer_account_id"], unique=False
    )
    op.create_index(op.f("ix_orders_status"), "orders", ["status"], unique=False)
    op.create_index(
        op.f("ix_orders_payment_status"), "orders", ["payment_status"], unique=False
    )

    # ── resolve the orders <-> shipping_infos circular FK pair ────────
    op.create_foreign_key(
        "fk_shipping_infos_order_id",
        "shipping_infos",
        "orders",
        ["order_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_orders_shipping_info_id",
        "orders",
        "shipping_infos",
        ["shipping_info_id"],
        ["id"],
    )

    # ── order_items (snapshotted purchase lines, per seller) ──────────
    op.create_table(
        "order_items",
        sa.Column("order_id", sa.UUID(), nullable=False),
        sa.Column("seller_id", sa.UUID(), nullable=False),
        sa.Column("listing_id", sa.UUID(), nullable=False),
        sa.Column("product_variant_id", sa.UUID(), nullable=False),
        sa.Column("product_name", sa.String(length=255), nullable=False),
        sa.Column("variant_name", sa.String(length=255), nullable=True),
        sa.Column("unit_price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("subtotal", sa.Numeric(precision=12, scale=2), nullable=False),
        *_timestamps(),
        _uuid(),
        sa.ForeignKeyConstraint(["listing_id"], ["seller_listings.id"]),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["product_variant_id"], ["product_variants.id"]),
        sa.ForeignKeyConstraint(["seller_id"], ["sellers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_order_items_order_id"), "order_items", ["order_id"], unique=False
    )
    op.create_index(
        op.f("ix_order_items_seller_id"), "order_items", ["seller_id"], unique=False
    )
    op.create_index(
        op.f("ix_order_items_listing_id"), "order_items", ["listing_id"], unique=False
    )
    op.create_index(
        op.f("ix_order_items_product_variant_id"),
        "order_items",
        ["product_variant_id"],
        unique=False,
    )

    # ── seller_orders (per-seller fulfillment record of a paid order) ──
    op.create_table(
        "seller_orders",
        sa.Column("order_id", sa.UUID(), nullable=False),
        sa.Column("seller_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("rejected_reason", sa.Text(), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("shipped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        _uuid(),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["seller_id"], ["sellers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "order_id", "seller_id", name="uq_seller_orders_order_seller"
        ),
    )
    op.create_index(
        op.f("ix_seller_orders_order_id"),
        "seller_orders",
        ["order_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_seller_orders_seller_id"),
        "seller_orders",
        ["seller_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_seller_orders_status"),
        "seller_orders",
        ["status"],
        unique=False,
    )

    # ── shipments (physical delivery of a seller_order) ───────────────
    op.create_table(
        "shipments",
        sa.Column("seller_order_id", sa.UUID(), nullable=False),
        sa.Column("carrier", sa.String(length=60), nullable=True),
        sa.Column("tracking_number", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("shipped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        *_timestamps(),
        _uuid(),
        sa.ForeignKeyConstraint(["seller_order_id"], ["seller_orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_shipments_seller_order_id"),
        "shipments",
        ["seller_order_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_shipments_status"), "shipments", ["status"], unique=False
    )

    # ── payments (money-in via Airtel Money, kept separate from orders) ─
    op.create_table(
        "payments",
        sa.Column("order_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("momo_phone", sa.String(length=20), nullable=True),
        sa.Column("airtel_phone", sa.String(length=20), nullable=True),
        sa.Column("method", sa.String(length=30), nullable=True),
        sa.Column("provider_ref", sa.String(length=255), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        _uuid(),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_payments_order_id"), "payments", ["order_id"], unique=False
    )
    op.create_index(op.f("ix_payments_status"), "payments", ["status"], unique=False)

    # ── revenue_transactions (the accounting record, one per order+seller)
    op.create_table(
        "revenue_transactions",
        sa.Column("order_id", sa.UUID(), nullable=False),
        sa.Column("payment_id", sa.UUID(), nullable=False),
        sa.Column("seller_id", sa.UUID(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("revenue_rate", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("commission_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("seller_earning", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("referral_eligible", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        _uuid(),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"]),
        sa.ForeignKeyConstraint(["seller_id"], ["sellers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "order_id", "seller_id", name="uq_revenue_transactions_order_seller"
        ),
    )
    op.create_index(
        op.f("ix_revenue_transactions_order_id"),
        "revenue_transactions",
        ["order_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_revenue_transactions_payment_id"),
        "revenue_transactions",
        ["payment_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_revenue_transactions_seller_id"),
        "revenue_transactions",
        ["seller_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_revenue_transactions_status"),
        "revenue_transactions",
        ["status"],
        unique=False,
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(
        op.f("ix_revenue_transactions_seller_id"),
        table_name="revenue_transactions",
    )
    op.drop_index(
        op.f("ix_revenue_transactions_status"),
        table_name="revenue_transactions",
    )
    op.drop_index(
        op.f("ix_revenue_transactions_payment_id"),
        table_name="revenue_transactions",
    )
    op.drop_index(
        op.f("ix_revenue_transactions_order_id"),
        table_name="revenue_transactions",
    )
    op.drop_table("revenue_transactions")
    op.drop_index(op.f("ix_payments_status"), table_name="payments")
    op.drop_index(op.f("ix_payments_order_id"), table_name="payments")
    op.drop_table("payments")
    op.drop_index(op.f("ix_shipments_status"), table_name="shipments")
    op.drop_index(op.f("ix_shipments_seller_order_id"), table_name="shipments")
    op.drop_table("shipments")
    op.drop_index(op.f("ix_seller_orders_status"), table_name="seller_orders")
    op.drop_index(op.f("ix_seller_orders_seller_id"), table_name="seller_orders")
    op.drop_index(op.f("ix_seller_orders_order_id"), table_name="seller_orders")
    op.drop_table("seller_orders")
    op.drop_index(
        op.f("ix_order_items_product_variant_id"), table_name="order_items"
    )
    op.drop_index(op.f("ix_order_items_listing_id"), table_name="order_items")
    op.drop_index(op.f("ix_order_items_seller_id"), table_name="order_items")
    op.drop_index(op.f("ix_order_items_order_id"), table_name="order_items")
    op.drop_table("order_items")
    op.drop_foreign_key("fk_orders_shipping_info_id", table_name="orders")
    op.drop_foreign_key("fk_shipping_infos_order_id", table_name="shipping_infos")
    op.drop_index(op.f("ix_orders_payment_status"), table_name="orders")
    op.drop_index(op.f("ix_orders_status"), table_name="orders")
    op.drop_index(op.f("ix_orders_buyer_account_id"), table_name="orders")
    op.drop_index(op.f("ix_orders_order_number"), table_name="orders")
    op.drop_table("orders")
    op.drop_index(op.f("ix_shipping_infos_order_id"), table_name="shipping_infos")
    op.drop_table("shipping_infos")
    op.drop_index(op.f("ix_cart_items_listing_id"), table_name="cart_items")
    op.drop_index(op.f("ix_cart_items_account_id"), table_name="cart_items")
    op.drop_table("cart_items")
    op.drop_index(op.f("ix_shipping_addresses_account_id"), table_name="shipping_addresses")
    op.drop_table("shipping_addresses")
    # ### end Alembic commands ###
