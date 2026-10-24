"""add service details: where, duration, notice, areas, working hours

Revision ID: 0012
Revises: 0011
Create Date: 2026-10-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

LOCATIONS = "('at_customer', 'at_provider', 'online')"
PLACE_PARTS = ("province", "district", "sector")


def _created_at() -> sa.Column:
    return sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )


def upgrade() -> None:
    # ── products: the service details ────────────────────────────────────
    # A service published before this has none: it takes no requests until
    # its seller completes it (README §7.5).
    op.add_column("products", sa.Column("service_location", sa.String(length=20), nullable=True))
    op.add_column("products", sa.Column("service_duration_minutes", sa.Integer(), nullable=True))
    op.add_column("products", sa.Column("service_min_notice_hours", sa.Integer(), nullable=True))
    op.create_check_constraint(
        op.f("ck_products_service_location_valid"),
        "products",
        f"service_location IS NULL OR service_location IN {LOCATIONS}",
    )
    op.create_check_constraint(
        op.f("ck_products_service_details_only_on_services"),
        "products",
        "kind = 'service' OR num_nonnulls(service_location, service_duration_minutes, "
        "service_min_notice_hours) = 0",
    )
    op.create_check_constraint(
        op.f("ck_products_service_numbers_valid"),
        "products",
        "service_duration_minutes > 0 AND service_min_notice_hours >= 0",
    )

    op.create_table(
        "product_service_areas",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("district", sa.String(length=100), nullable=False),
        _created_at(),
        sa.PrimaryKeyConstraint("id", name="pk_product_service_areas"),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name="fk_product_service_areas_product_id_products",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "product_id", "district", name="uq_product_service_areas_product_id_district"
        ),
    )
    op.create_index(
        "ix_product_service_areas_lower_district",
        "product_service_areas",
        [sa.text("lower(district)")],
    )

    op.create_table(
        "product_service_hours",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("weekday", sa.Integer(), nullable=False),
        sa.Column("opens_at", sa.Time(), nullable=False),
        sa.Column("closes_at", sa.Time(), nullable=False),
        _created_at(),
        sa.PrimaryKeyConstraint("id", name="pk_product_service_hours"),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name="fk_product_service_hours_product_id_products",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "product_id", "weekday", name="uq_product_service_hours_product_id_weekday"
        ),
        sa.CheckConstraint(
            "weekday BETWEEN 1 AND 7", name=op.f("ck_product_service_hours_weekday_valid")
        ),
        sa.CheckConstraint(
            "opens_at < closes_at", name=op.f("ck_product_service_hours_opens_before_closing")
        ),
    )

    # ── orders: where a service order is done; no place unless at_customer ─
    # Every service order so far was done at the buyer's place.
    op.add_column("orders", sa.Column("service_location", sa.String(length=20), nullable=True))
    op.execute("UPDATE orders SET service_location = 'at_customer' WHERE kind = 'service'")
    for part in PLACE_PARTS:
        op.alter_column(
            "orders", f"delivery_{part}", existing_type=sa.String(length=100), nullable=True
        )
    op.create_check_constraint(
        op.f("ck_orders_service_location_matches_kind"),
        "orders",
        "(kind = 'service') = (service_location IS NOT NULL)",
    )
    op.create_check_constraint(
        op.f("ck_orders_place_complete"),
        "orders",
        "num_nonnulls(delivery_province, delivery_district, delivery_sector) IN (0, 3)",
    )
    op.create_check_constraint(
        op.f("ck_orders_place_matches_kind"),
        "orders",
        "(delivery_district IS NOT NULL) = (kind = 'product' OR service_location = 'at_customer')",
    )
    op.create_check_constraint(
        op.f("ck_orders_address_needs_place"),
        "orders",
        "delivery_district IS NOT NULL OR delivery_address IS NULL",
    )

    # ── service_requests: the same ───────────────────────────────────────
    op.add_column(
        "service_requests", sa.Column("service_location", sa.String(length=20), nullable=True)
    )
    op.execute("UPDATE service_requests SET service_location = 'at_customer'")
    op.alter_column(
        "service_requests",
        "service_location",
        existing_type=sa.String(length=20),
        nullable=False,
    )
    for part in PLACE_PARTS:
        op.alter_column(
            "service_requests", part, existing_type=sa.String(length=100), nullable=True
        )
    op.create_check_constraint(
        op.f("ck_service_requests_service_location_valid"),
        "service_requests",
        f"service_location IN {LOCATIONS}",
    )
    op.create_check_constraint(
        op.f("ck_service_requests_place_complete"),
        "service_requests",
        "num_nonnulls(province, district, sector) IN (0, 3)",
    )
    op.create_check_constraint(
        op.f("ck_service_requests_place_matches_location"),
        "service_requests",
        "(district IS NOT NULL) = (service_location = 'at_customer')",
    )
    op.create_check_constraint(
        op.f("ck_service_requests_address_needs_place"),
        "service_requests",
        "district IS NOT NULL OR address IS NULL",
    )


def downgrade() -> None:
    # Fails if a service order or request without a place exists: those
    # cannot be represented before this revision.
    for name in (
        "address_needs_place",
        "place_matches_location",
        "place_complete",
        "service_location_valid",
    ):
        op.drop_constraint(op.f(f"ck_service_requests_{name}"), "service_requests", type_="check")
    for part in PLACE_PARTS:
        op.alter_column(
            "service_requests", part, existing_type=sa.String(length=100), nullable=False
        )
    op.drop_column("service_requests", "service_location")

    for name in (
        "address_needs_place",
        "place_matches_kind",
        "place_complete",
        "service_location_matches_kind",
    ):
        op.drop_constraint(op.f(f"ck_orders_{name}"), "orders", type_="check")
    for part in PLACE_PARTS:
        op.alter_column(
            "orders", f"delivery_{part}", existing_type=sa.String(length=100), nullable=False
        )
    op.drop_column("orders", "service_location")

    op.drop_table("product_service_hours")
    op.drop_index("ix_product_service_areas_lower_district", table_name="product_service_areas")
    op.drop_table("product_service_areas")
    for name in ("service_numbers_valid", "service_details_only_on_services"):
        op.drop_constraint(op.f(f"ck_products_{name}"), "products", type_="check")
    op.drop_constraint(op.f("ck_products_service_location_valid"), "products", type_="check")
    op.drop_column("products", "service_min_notice_hours")
    op.drop_column("products", "service_duration_minutes")
    op.drop_column("products", "service_location")
