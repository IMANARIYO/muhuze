"""create product tables

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamp(name: str) -> sa.Column:
    return sa.Column(name, sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("seller_id", sa.Uuid(), nullable=False),
        sa.Column("category_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=220), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="RWF", nullable=False),
        sa.Column("status", sa.String(length=20), server_default="draft", nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("hidden_by_staff_at", sa.DateTime(timezone=True), nullable=True),
        _timestamp("created_at"),
        _timestamp("updated_at"),
        sa.PrimaryKeyConstraint("id", name="pk_products"),
        sa.ForeignKeyConstraint(
            ["seller_id"], ["sellers.id"], name="fk_products_seller_id_sellers", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            name="fk_products_category_id_categories",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("seller_id", "slug", name="uq_products_seller_id_slug"),
        sa.CheckConstraint(
            "status IN ('draft', 'published', 'archived')", name=op.f("ck_products_status_valid")
        ),
        sa.CheckConstraint("price >= 0", name=op.f("ck_products_price_not_negative")),
    )
    op.create_index("ix_products_seller_id_status", "products", ["seller_id", "status"])
    op.create_index("ix_products_category_id", "products", ["category_id"])
    op.create_index("ix_products_status_published_at", "products", ["status", "published_at"])

    op.create_table(
        "product_images",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("storage_public_id", sa.String(length=255), nullable=False),
        sa.Column("storage_format", sa.String(length=10), nullable=False),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        _timestamp("created_at"),
        sa.PrimaryKeyConstraint("id", name="pk_product_images"),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name="fk_product_images_product_id_products",
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_product_images_product_id", "product_images", ["product_id"])

    op.create_table(
        "product_attribute_values",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("attribute_id", sa.Uuid(), nullable=False),
        sa.Column("option_id", sa.Uuid(), nullable=True),
        sa.Column("value_text", sa.String(length=500), nullable=True),
        sa.Column("value_number", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("value_boolean", sa.Boolean(), nullable=True),
        _timestamp("created_at"),
        sa.PrimaryKeyConstraint("id", name="pk_product_attribute_values"),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name="fk_product_attribute_values_product_id_products",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["attribute_id"],
            ["category_attributes.id"],
            name="fk_product_attribute_values_attribute_id_category_attributes",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["option_id"],
            ["category_attribute_options.id"],
            name="fk_product_attribute_values_option_id_options",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "product_id",
            "attribute_id",
            "option_id",
            name="uq_product_attribute_values_product_id_attribute_id_option_id",
            postgresql_nulls_not_distinct=True,
        ),
        sa.CheckConstraint(
            "num_nonnulls(option_id, value_text, value_number, value_boolean) = 1",
            name=op.f("ck_product_attribute_values_exactly_one_value"),
        ),
    )
    op.create_index(
        "ix_product_attribute_values_attribute_id_option_id",
        "product_attribute_values",
        ["attribute_id", "option_id"],
    )
    op.create_index(
        "ix_product_attribute_values_attribute_id_value_number",
        "product_attribute_values",
        ["attribute_id", "value_number"],
    )


def downgrade() -> None:
    op.drop_table("product_attribute_values")
    op.drop_table("product_images")
    op.drop_table("products")
