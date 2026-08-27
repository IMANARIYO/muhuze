import uuid
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDPKMixin

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class BrandStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class AttributeStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class AttributeInputType(StrEnum):
    SELECT = "select"
    TEXT = "text"
    NUMBER = "number"


class ProductStatus(StrEnum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    ACTIVE = "active"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class VariantStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class ListingCondition(StrEnum):
    NEW = "new"
    LIKE_NEW = "like_new"
    USED = "used"


class ListingStatus(StrEnum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    ACTIVE = "active"
    REJECTED = "rejected"
    SUSPENDED = "suspended"
    OUT_OF_STOCK = "out_of_stock"
    ARCHIVED = "archived"


# ---------------------------------------------------------------------------
# Catalog: brands, attributes, category_attributes
# ---------------------------------------------------------------------------


class Brand(UUIDPKMixin, TimestampMixin, Base):
    """Brand registry — Samsung, Nike, etc. Admin-managed. Never hard-deleted
    once products reference it; lifecycle is status-only."""

    __tablename__ = "brands"

    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(
        String(170), unique=True, nullable=False, index=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=BrandStatus.ACTIVE, index=True
    )


class Attribute(UUIDPKMixin, TimestampMixin, Base):
    """Attribute definition — Color, Size, RAM, etc. Admin-managed. Defines
    *what can vary* but not the actual values (those live in
    variant_attribute_values)."""

    __tablename__ = "attributes"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(120), unique=True, nullable=False, index=True
    )
    input_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default=AttributeInputType.SELECT
    )
    unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=AttributeStatus.ACTIVE, index=True
    )


class CategoryAttribute(UUIDPKMixin, TimestampMixin, Base):
    """Junction between categories and attributes. Defines which attributes
    apply to a category, whether they are required, variant-defining, or
    filterable. Drives both the seller listing flow and buyer search."""

    __tablename__ = "category_attributes"
    __table_args__ = (
        UniqueConstraint(
            "category_id",
            "attribute_id",
            name="uq_category_attributes_category_attribute",
        ),
    )

    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id"),
        nullable=False,
        index=True,
    )
    attribute_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("attributes.id"),
        nullable=False,
        index=True,
    )
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_variant: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_filterable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


# ---------------------------------------------------------------------------
# Product catalog: products, product_variants, variant_attribute_values,
#                   product_images
# ---------------------------------------------------------------------------


class Product(UUIDPKMixin, TimestampMixin, Base):
    """SPU (Standard Product Unit) — the canonical marketplace entry. Does NOT
    contain price, stock, or seller information; those live in
    seller_listings. A product belongs to exactly one category and optionally
    one brand. Never hard-deleted once it has order history."""

    __tablename__ = "products"

    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id"),
        nullable=False,
        index=True,
    )
    brand_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brands.id"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(280), unique=True, nullable=False, index=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ProductStatus.DRAFT, index=True
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class ProductVariant(UUIDPKMixin, TimestampMixin, Base):
    """SKU (Stock Keeping Unit) — a specific version of a product, defined by
    its combination of attribute values in variant_attribute_values. Multiple
    sellers can offer the same variant at different prices through
    seller_listings."""

    __tablename__ = "product_variants"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sku_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=VariantStatus.ACTIVE, index=True
    )


class VariantAttributeValue(UUIDPKMixin, TimestampMixin, Base):
    """The actual attribute value that defines a variant. Bridge between
    abstract attribute definitions and concrete variant values. Enables
    filtering ("show me all variants where Color = Black") and uniqueness
    enforcement (same attribute combination = same variant)."""

    __tablename__ = "variant_attribute_values"
    __table_args__ = (
        UniqueConstraint(
            "variant_id",
            "attribute_id",
            name="uq_variant_attribute_values_variant_attribute",
        ),
    )

    variant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_variants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attribute_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("attributes.id"),
        nullable=False,
        index=True,
    )
    value: Mapped[str] = mapped_column(String(255), nullable=False)


class ProductImage(UUIDPKMixin, TimestampMixin, Base):
    """Canonical product image — stock photos, brand images. Represents the
    product itself, not a specific seller's actual stock. Follows the same
    Cloudinary pattern as seller_documents: no public URL stored; access is
    through freshly-signed URLs."""

    __tablename__ = "product_images"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cloudinary_public_id: Mapped[str] = mapped_column(String(255), nullable=False)
    cloudinary_resource_type: Mapped[str] = mapped_column(String(20), nullable=False)
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


# ---------------------------------------------------------------------------
# Seller bridge: seller_listings, listing_images
# ---------------------------------------------------------------------------


class SellerListing(UUIDPKMixin, TimestampMixin, Base):
    """A seller's offer for a specific variant. This is the bridge between the
    catalog and the seller. It answers: "How is this seller selling this
    variant?" Unique on (seller_id, variant_id) — one listing per seller per
    variant. Feeds into the financial architecture: listing → order → payment
    → revenue → wallet."""

    __tablename__ = "seller_listings"
    __table_args__ = (
        UniqueConstraint(
            "seller_id",
            "variant_id",
            name="uq_seller_listings_seller_variant",
        ),
    )

    seller_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sellers.id"),
        nullable=False,
        index=True,
    )
    variant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_variants.id"),
        nullable=False,
        index=True,
    )
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    seller_sku: Mapped[str | None] = mapped_column(String(100), nullable=True)
    condition: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ListingCondition.NEW
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ListingStatus.DRAFT, index=True
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class ListingImage(UUIDPKMixin, TimestampMixin, Base):
    """Seller-specific product photos — shows the seller's actual stock. These
    are distinct from product_images (canonical/stock photos). Follows the
    same Cloudinary pattern as seller_documents."""

    __tablename__ = "listing_images"

    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("seller_listings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cloudinary_public_id: Mapped[str] = mapped_column(String(255), nullable=False)
    cloudinary_resource_type: Mapped[str] = mapped_column(String(20), nullable=False)
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
