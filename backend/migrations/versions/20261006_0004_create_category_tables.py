"""create category tables

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamp(name: str) -> sa.Column:
    return sa.Column(name, sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("seller_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("hidden_by_staff_at", sa.DateTime(timezone=True), nullable=True),
        _timestamp("created_at"),
        _timestamp("updated_at"),
        sa.PrimaryKeyConstraint("id", name="pk_categories"),
        sa.ForeignKeyConstraint(
            ["seller_id"],
            ["sellers.id"],
            name="fk_categories_seller_id_sellers",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("seller_id", "slug", name="uq_categories_seller_id_slug"),
    )
    op.create_index(
        "uq_categories_seller_id_name_lower",
        "categories",
        ["seller_id", sa.text("lower(name)")],
        unique=True,
    )

    op.create_table(
        "category_attributes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("category_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("data_type", sa.String(length=20), nullable=False),
        sa.Column("unit", sa.String(length=20), nullable=True),
        sa.Column("is_required", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("is_filterable", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        _timestamp("created_at"),
        _timestamp("updated_at"),
        sa.PrimaryKeyConstraint("id", name="pk_category_attributes"),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            name="fk_category_attributes_category_id_categories",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("category_id", "code", name="uq_category_attributes_category_id_code"),
        sa.CheckConstraint(
            "data_type IN ('text', 'number', 'boolean', 'select', 'multi_select')",
            name=op.f("ck_category_attributes_data_type_valid"),
        ),
    )

    op.create_table(
        "category_attribute_options",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("attribute_id", sa.Uuid(), nullable=False),
        sa.Column("value", sa.String(length=100), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        _timestamp("created_at"),
        _timestamp("updated_at"),
        sa.PrimaryKeyConstraint("id", name="pk_category_attribute_options"),
        sa.ForeignKeyConstraint(
            ["attribute_id"],
            ["category_attributes.id"],
            name="fk_category_attribute_options_attribute_id_category_attributes",
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "uq_category_attribute_options_attribute_id_value_lower",
        "category_attribute_options",
        ["attribute_id", sa.text("lower(value)")],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("category_attribute_options")
    op.drop_table("category_attributes")
    op.drop_table("categories")
