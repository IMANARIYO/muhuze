import uuid

from pydantic import BaseModel, ConfigDict, Field


class CatalogProductRef(BaseModel):
    """The canonical product this listing/variant belongs to — enough for
    a card or detail page without needing a separate /products call."""

    id: uuid.UUID = Field(description="Product (SPU) ID")
    name: str = Field(description="Product name")
    slug: str = Field(description="URL-safe slug (auto-generated from name)")
    description: str | None = Field(description="Product description")
    category_id: uuid.UUID = Field(description="Category this product belongs to")


class CatalogVariantAttribute(BaseModel):
    """One attribute-value pair that defines a variant (e.g. Color=Black)."""

    attribute_id: uuid.UUID = Field(description="Attribute ID")
    attribute_name: str = Field(description="Attribute name (e.g. 'Color')")
    value: str = Field(description="Attribute value (e.g. 'Black')")


class CatalogVariantRef(BaseModel):
    """A variant (SKU) with its defining attribute values."""

    id: uuid.UUID = Field(description="Variant (SKU) ID")
    sku_code: str | None = Field(description="SKU code (if set)")
    attribute_values: list[CatalogVariantAttribute] = Field(
        description="Attribute-value pairs that define this variant"
    )


class CatalogSellerRef(BaseModel):
    """The active seller offering this listing."""

    id: uuid.UUID = Field(description="Seller profile ID")
    business_name: str = Field(description="Business or shop name")


class CatalogImage(BaseModel):
    """A canonical public product image."""

    id: uuid.UUID = Field(description="Image ID")
    url: str = Field(description="Public Cloudinary URL")
    is_primary: bool = Field(description="Whether this is the primary image")
    sort_order: int = Field(description="Display sort order (0-based)")


class CatalogListingItem(BaseModel):
    """One buyable row in the buyer catalog — an active listing joined
    with its variant, product, and seller. This is what a buyer sees and
    orders against; `listing_id` is what you'd pass at checkout."""

    model_config = ConfigDict(from_attributes=True)

    listing_id: uuid.UUID = Field(description="Listing ID (the buyable offer)")
    price: float = Field(description="Selling price offered by this seller")
    stock: int = Field(description="Available stock")
    condition: str = Field(description="Item condition: 'new', 'like_new', or 'used'")
    product: CatalogProductRef = Field(
        description="The canonical product this offer belongs to"
    )
    variant: CatalogVariantRef = Field(
        description="The specific variant (SKU) being offered"
    )
    seller: CatalogSellerRef = Field(description="The seller making this offer")
    images: list[CatalogImage] = Field(
        description="Canonical product images (public, CDN-served)"
    )


class CatalogOffer(BaseModel):
    """One seller's offer for a specific variant on a product detail page."""

    listing_id: uuid.UUID = Field(description="Listing ID (the buyable offer)")
    price: float = Field(description="Selling price")
    stock: int = Field(description="Available stock")
    condition: str = Field(description="Item condition: 'new', 'like_new', or 'used'")
    seller: CatalogSellerRef = Field(description="The seller making this offer")


class CatalogVariantDetail(BaseModel):
    """A variant on the product detail page, with every current seller
    offering it."""

    id: uuid.UUID = Field(description="Variant (SKU) ID")
    sku_code: str | None = Field(description="SKU code (if set)")
    attribute_values: list[CatalogVariantAttribute] = Field(
        description="Attribute-value pairs that define this variant"
    )
    offers: list[CatalogOffer] = Field(
        description="Current active sellers offering this variant, with price/stock"
    )


class CatalogProductDetail(BaseModel):
    """Full buyer-facing product detail: the product, its images, every
    active variant, and all active sellers offering each variant."""

    id: uuid.UUID = Field(description="Product (SPU) ID")
    name: str = Field(description="Product name")
    slug: str = Field(description="URL-safe slug")
    description: str | None = Field(description="Product description")
    category_id: uuid.UUID = Field(description="Category this product belongs to")
    brand_id: uuid.UUID | None = Field(description="Brand ID (if assigned)")
    images: list[CatalogImage] = Field(
        description="Canonical product images (public, CDN-served)"
    )
    variants: list[CatalogVariantDetail] = Field(
        description="Every active variant, each with its current seller offers"
    )
