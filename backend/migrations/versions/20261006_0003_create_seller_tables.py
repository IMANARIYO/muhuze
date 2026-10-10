"""create seller tables

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamp(name: str) -> sa.Column:
    return sa.Column(name, sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)


def upgrade() -> None:
    op.create_table(
        "sellers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("business_name", sa.String(length=150), nullable=False),
        sa.Column("business_description", sa.Text(), nullable=True),
        sa.Column("business_phone", sa.String(length=20), nullable=False),
        sa.Column("identity_document_type", sa.String(length=20), nullable=False),
        sa.Column("identity_document_number", sa.String(length=50), nullable=False),
        sa.Column("country_code", sa.String(length=2), server_default="RW", nullable=False),
        sa.Column("province", sa.String(length=100), nullable=False),
        sa.Column("district", sa.String(length=100), nullable=False),
        sa.Column("sector", sa.String(length=100), nullable=False),
        sa.Column("cell", sa.String(length=100), nullable=True),
        sa.Column("village", sa.String(length=100), nullable=True),
        sa.Column("street_address", sa.String(length=255), nullable=True),
        sa.Column("latitude", sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column("longitude", sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column("location_accuracy_m", sa.Integer(), nullable=True),
        sa.Column("location_source", sa.String(length=20), nullable=True),
        sa.Column("location_captured_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="draft", nullable=False),
        sa.Column("status_reason", sa.String(length=500), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by_account_id", sa.Uuid(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        _timestamp("created_at"),
        _timestamp("updated_at"),
        sa.PrimaryKeyConstraint("id", name="pk_sellers"),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name="fk_sellers_account_id_accounts",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by_account_id"],
            ["accounts.id"],
            name="fk_sellers_reviewed_by_account_id_accounts",
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint("account_id", name="uq_sellers_account_id"),
        sa.CheckConstraint(
            "status IN ('draft', 'pending_review', 'active', 'rejected', "
            "'suspended', 'deactivated')",
            name=op.f("ck_sellers_status_valid"),
        ),
        sa.CheckConstraint(
            "identity_document_type IN ('national_id', 'passport', 'driving_license')",
            name=op.f("ck_sellers_identity_document_type_valid"),
        ),
        sa.CheckConstraint(
            "location_source IS NULL OR location_source IN ('device', 'manual')",
            name=op.f("ck_sellers_location_source_valid"),
        ),
        sa.CheckConstraint(
            "(latitude IS NULL) = (longitude IS NULL)",
            name=op.f("ck_sellers_coordinates_both_or_neither"),
        ),
        sa.CheckConstraint(
            "latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180",
            name=op.f("ck_sellers_coordinates_in_range"),
        ),
    )
    op.create_index(
        "uq_sellers_business_name_lower", "sellers", [sa.text("lower(business_name)")], unique=True
    )
    op.create_index("ix_sellers_status", "sellers", ["status"])

    op.create_table(
        "seller_documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("seller_id", sa.Uuid(), nullable=False),
        sa.Column("document_type", sa.String(length=30), nullable=False),
        sa.Column("storage_public_id", sa.String(length=255), nullable=False),
        sa.Column("storage_resource_type", sa.String(length=20), nullable=False),
        sa.Column("storage_format", sa.String(length=10), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=True),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        _timestamp("created_at"),
        _timestamp("updated_at"),
        sa.PrimaryKeyConstraint("id", name="pk_seller_documents"),
        sa.ForeignKeyConstraint(
            ["seller_id"],
            ["sellers.id"],
            name="fk_seller_documents_seller_id_sellers",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "seller_id", "document_type", name="uq_seller_documents_seller_id_document_type"
        ),
        sa.CheckConstraint(
            "document_type IN ('identity_front', 'identity_back', "
            "'business_registration', 'tin_certificate')",
            name=op.f("ck_seller_documents_document_type_valid"),
        ),
    )

    op.create_table(
        "seller_status_history",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("seller_id", sa.Uuid(), nullable=False),
        sa.Column("from_status", sa.String(length=20), nullable=True),
        sa.Column("to_status", sa.String(length=20), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=True),
        sa.Column("changed_by_account_id", sa.Uuid(), nullable=True),
        _timestamp("created_at"),
        sa.PrimaryKeyConstraint("id", name="pk_seller_status_history"),
        sa.ForeignKeyConstraint(
            ["seller_id"],
            ["sellers.id"],
            name="fk_seller_status_history_seller_id_sellers",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["changed_by_account_id"],
            ["accounts.id"],
            name="fk_seller_status_history_changed_by_account_id_accounts",
            ondelete="SET NULL",
        ),
    )
    op.create_index("ix_seller_status_history_seller_id", "seller_status_history", ["seller_id"])


def downgrade() -> None:
    op.drop_table("seller_status_history")
    op.drop_table("seller_documents")
    op.drop_table("sellers")
