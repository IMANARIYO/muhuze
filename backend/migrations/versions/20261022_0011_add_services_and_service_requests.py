"""add services: listing kind, service orders, and service requests

Revision ID: 0011
Revises: 0010
Create Date: 2026-10-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

KINDS = "kind IN ('product', 'service')"


def _timestamp(name: str) -> sa.Column:
    return sa.Column(name, sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)


def upgrade() -> None:
    # Every existing listing is goods, and every existing order a checkout.
    op.add_column(
        "products",
        sa.Column("kind", sa.String(length=20), server_default="product", nullable=False),
    )
    op.create_check_constraint(op.f("ck_products_kind_valid"), "products", KINDS)

    op.add_column(
        "orders",
        sa.Column("kind", sa.String(length=20), server_default="product", nullable=False),
    )
    op.add_column("orders", sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True))
    op.create_check_constraint(op.f("ck_orders_kind_valid"), "orders", KINDS)
    op.create_check_constraint(
        op.f("ck_orders_scheduled_for_matches_kind"),
        "orders",
        "(kind = 'service') = (scheduled_for IS NOT NULL)",
    )

    op.create_table(
        "service_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("buyer_account_id", sa.Uuid(), nullable=False),
        sa.Column("seller_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("service_name", sa.String(length=200), nullable=False),
        sa.Column("seller_name", sa.String(length=150), nullable=False),
        sa.Column("unit_price", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="RWF", nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("contact_name", sa.String(length=150), nullable=False),
        sa.Column("contact_phone", sa.String(length=20), nullable=False),
        sa.Column("province", sa.String(length=100), nullable=False),
        sa.Column("district", sa.String(length=100), nullable=False),
        sa.Column("sector", sa.String(length=100), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="requested", nullable=False),
        sa.Column("status_reason", sa.String(length=500), nullable=True),
        sa.Column("responded_by_account_id", sa.Uuid(), nullable=True),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("order_id", sa.Uuid(), nullable=True),
        _timestamp("created_at"),
        _timestamp("updated_at"),
        sa.PrimaryKeyConstraint("id", name="pk_service_requests"),
        sa.ForeignKeyConstraint(
            ["buyer_account_id"],
            ["accounts.id"],
            name="fk_service_requests_buyer_account_id_accounts",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["seller_id"],
            ["sellers.id"],
            name="fk_service_requests_seller_id_sellers",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name="fk_service_requests_product_id_products",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["responded_by_account_id"],
            ["accounts.id"],
            name="fk_service_requests_responded_by_account_id_accounts",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"],
            name="fk_service_requests_order_id_orders",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("order_id", name="uq_service_requests_order_id"),
        sa.CheckConstraint(
            "status IN ('requested', 'accepted', 'declined', 'cancelled')",
            name=op.f("ck_service_requests_status_valid"),
        ),
        sa.CheckConstraint("unit_price >= 0", name=op.f("ck_service_requests_price_not_negative")),
        sa.CheckConstraint(
            "(status = 'accepted') = (order_id IS NOT NULL)",
            name=op.f("ck_service_requests_order_only_when_accepted"),
        ),
    )
    op.create_index(
        "ix_service_requests_buyer_account_id_created_at",
        "service_requests",
        ["buyer_account_id", "created_at"],
    )
    op.create_index(
        "ix_service_requests_seller_id_status_created_at",
        "service_requests",
        ["seller_id", "status", "created_at"],
    )
    op.create_index("ix_service_requests_product_id", "service_requests", ["product_id"])


def downgrade() -> None:
    op.drop_table("service_requests")
    op.drop_constraint(op.f("ck_orders_scheduled_for_matches_kind"), "orders", type_="check")
    op.drop_constraint(op.f("ck_orders_kind_valid"), "orders", type_="check")
    op.drop_column("orders", "scheduled_for")
    op.drop_column("orders", "kind")
    op.drop_constraint(op.f("ck_products_kind_valid"), "products", type_="check")
    op.drop_column("products", "kind")
