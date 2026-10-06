"""Persistence models for products.

Mirrors `docs/database/database_schema.dbml`; change both together.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.modules.products.product_constants import (
    ATTRIBUTE_TEXT_MAX_LENGTH,
    DEFAULT_CURRENCY,
    PRICE_DECIMAL_PLACES,
    PRICE_MAX_DIGITS,
    PRODUCT_NAME_MAX_LENGTH,
    PRODUCT_SLUG_MAX_LENGTH,
    ProductStatus,
)


class Product(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """What a seller offers for sale: the fields every product has. Anything
    specific to a kind of product is a ProductAttributeValue (README §7.3)."""

    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("seller_id", "slug"),
        CheckConstraint(
            f"status IN ({', '.join(repr(s.value) for s in ProductStatus)})", name="status_valid"
        ),
        CheckConstraint("price >= 0", name="price_not_negative"),
        Index("ix_products_seller_id_status", "seller_id", "status"),
        Index("ix_products_category_id", "category_id"),
        Index("ix_products_status_published_at", "status", "published_at"),
    )

    seller_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sellers.id", ondelete="RESTRICT"))
    # RESTRICT: a category that still has products cannot be deleted.
    category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"))
    name: Mapped[str] = mapped_column(String(PRODUCT_NAME_MAX_LENGTH))
    slug: Mapped[str] = mapped_column(String(PRODUCT_SLUG_MAX_LENGTH))
    description: Mapped[str | None] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(PRICE_MAX_DIGITS, PRICE_DECIMAL_PLACES))
    currency: Mapped[str] = mapped_column(
        String(3), default=DEFAULT_CURRENCY, server_default=DEFAULT_CURRENCY
    )
    status: Mapped[str] = mapped_column(
        String(20), default=ProductStatus.DRAFT.value, server_default=ProductStatus.DRAFT.value
    )
    # First publication. Never cleared: once set, the product can't be deleted.
    published_at: Mapped[datetime | None]
    # Set when staff hide the product; buyers don't see it and the seller
    # cannot publish it.
    hidden_by_staff_at: Mapped[datetime | None]


class ProductImage(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """A public picture of a product. The lowest sort_order is the main image."""

    __tablename__ = "product_images"

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    storage_public_id: Mapped[str] = mapped_column(String(255))
    storage_format: Mapped[str] = mapped_column(String(10))
    width: Mapped[int | None]
    height: Mapped[int | None]
    sort_order: Mapped[int] = mapped_column(default=0, server_default="0")


class ProductAttributeValue(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """A product's value for one attribute of its category.

    text / number / boolean → one row with the matching value_* column set;
    select → one row pointing at the chosen option; multi_select → one row
    per chosen option. Exactly one of the four value columns is set.

    RESTRICT on attribute and option: what products use cannot be deleted,
    only switched off (README §20 K8).
    """

    __tablename__ = "product_attribute_values"
    __table_args__ = (
        # NULLS NOT DISTINCT: scalar values (option_id NULL) are also limited
        # to one row per attribute.
        UniqueConstraint(
            "product_id", "attribute_id", "option_id", postgresql_nulls_not_distinct=True
        ),
        CheckConstraint(
            "num_nonnulls(option_id, value_text, value_number, value_boolean) = 1",
            name="exactly_one_value",
        ),
        Index("ix_product_attribute_values_attribute_id_option_id", "attribute_id", "option_id"),
        Index(
            "ix_product_attribute_values_attribute_id_value_number", "attribute_id", "value_number"
        ),
    )

    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    attribute_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("category_attributes.id", ondelete="RESTRICT")
    )
    option_id: Mapped[uuid.UUID | None] = mapped_column(
        # Named by hand: the conventional name is one character over
        # PostgreSQL's 63-character limit.
        ForeignKey(
            "category_attribute_options.id",
            ondelete="RESTRICT",
            name="fk_product_attribute_values_option_id_options",
        )
    )
    value_text: Mapped[str | None] = mapped_column(String(ATTRIBUTE_TEXT_MAX_LENGTH))
    value_number: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    value_boolean: Mapped[bool | None] = mapped_column(Boolean)
