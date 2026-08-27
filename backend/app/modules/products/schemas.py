import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# --- brands ------------------------------------------------------------------


class BrandCreateRequest(BaseModel):
    name: str = Field(
        min_length=1, max_length=150, description="Brand name (must be unique)"
    )
    description: str | None = Field(
        default=None, description="Optional brand description"
    )


class BrandUpdateRequest(BaseModel):
    name: str = Field(
        min_length=1, max_length=150, description="Brand name (must be unique)"
    )
    description: str | None = Field(
        default=None, description="Optional brand description"
    )
    status: Literal["active", "inactive"] = Field(
        description="Brand status: 'active' or 'inactive'"
    )


class BrandResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Brand ID")
    name: str = Field(description="Brand name")
    slug: str = Field(description="URL-safe slug (auto-generated from name)")
    description: str | None = Field(description="Brand description")
    status: str = Field(description="Brand status: 'active' or 'inactive'")
    created_at: datetime = Field(description="When the brand was created (UTC)")
    updated_at: datetime = Field(description="When the brand was last updated (UTC)")


# --- attributes ----------------------------------------------------------


class AttributeCreateRequest(BaseModel):
    name: str = Field(
        min_length=1, max_length=100, description="Attribute name (e.g. 'Color', 'RAM')"
    )
    input_type: Literal["select", "text", "number", "boolean"] = Field(
        default="select",
        description="How sellers input values: 'select', 'text', 'number', or 'boolean'",
    )
    unit: str | None = Field(
        default=None, description="Optional unit (e.g. 'GB', 'mm')"
    )


class AttributeUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100, description="Attribute name")
    input_type: Literal["select", "text", "number", "boolean"] = Field(
        description="How sellers input values: 'select', 'text', 'number', or 'boolean'"
    )
    unit: str | None = Field(default=None, description="Optional unit")
    status: Literal["active", "inactive"] = Field(
        description="Attribute status: 'active' or 'inactive'"
    )


class AttributeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Attribute ID")
    name: str = Field(description="Attribute name")
    slug: str = Field(description="URL-safe slug (auto-generated from name)")
    input_type: str = Field(
        description="Input type: 'select', 'text', 'number', or 'boolean'"
    )
    unit: str | None = Field(description="Optional unit (e.g. 'GB', 'mm')")
    status: str = Field(description="Attribute status: 'active' or 'inactive'")
    created_at: datetime = Field(description="When the attribute was created (UTC)")
    updated_at: datetime = Field(
        description="When the attribute was last updated (UTC)"
    )


# --- products --------------------------------------------------------------


class ProductCreateRequest(BaseModel):
    category_id: uuid.UUID = Field(description="Category ID this product belongs to")
    brand_id: uuid.UUID | None = Field(default=None, description="Optional brand ID")
    name: str = Field(min_length=1, max_length=255, description="Product name")
    description: str | None = Field(
        default=None, description="Optional product description"
    )


class ProductUpdateRequest(BaseModel):
    category_id: uuid.UUID = Field(description="Category ID this product belongs to")
    brand_id: uuid.UUID | None = Field(default=None, description="Optional brand ID")
    name: str = Field(min_length=1, max_length=255, description="Product name")
    description: str | None = Field(
        default=None, description="Optional product description"
    )


class RejectProductRequest(BaseModel):
    reason: str = Field(
        min_length=1, description="Admin reason for rejecting this product"
    )


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Product ID")
    category_id: uuid.UUID = Field(description="Category ID")
    brand_id: uuid.UUID | None = Field(description="Brand ID (if assigned)")
    created_by_seller_id: uuid.UUID | None = Field(
        description="Seller who requested this product, if any (null means admin-curated)"
    )
    name: str = Field(description="Product name")
    slug: str = Field(description="URL-safe slug (auto-generated from name)")
    description: str | None = Field(description="Product description")
    status: str = Field(
        description=(
            "Product status: 'draft', 'pending_review', 'active', "
            "'rejected', or 'archived'"
        )
    )
    rejection_reason: str | None = Field(
        description="Reason for rejection (set when status is 'rejected')"
    )
    created_at: datetime = Field(description="When the product was created (UTC)")
    updated_at: datetime = Field(description="When the product was last updated (UTC)")


# --- variants ----------------------------------------------------------------


class VariantAttributeValueInput(BaseModel):
    attribute_id: uuid.UUID = Field(description="Attribute ID (e.g. Color)")
    value: str = Field(min_length=1, max_length=255, description="Value (e.g. 'Black')")


class ProductVariantCreateRequest(BaseModel):
    sku_code: str | None = Field(
        default=None, max_length=50, description="Optional SKU code for this variant"
    )
    attribute_values: list[VariantAttributeValueInput] = Field(
        default_factory=list,
        description="Attribute-value pairs defining this variant (e.g. Color=Black)",
    )


class ProductVariantUpdateRequest(BaseModel):
    sku_code: str | None = Field(default=None, max_length=50, description="SKU code")
    status: Literal["active", "inactive"] = Field(
        description="Variant status: 'active' or 'inactive'"
    )


class VariantAttributeValueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    attribute_id: uuid.UUID = Field(description="Attribute ID")
    value: str = Field(description="Attribute value")


class ProductVariantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Variant ID")
    product_id: uuid.UUID = Field(description="Parent product ID")
    sku_code: str | None = Field(description="SKU code (if set)")
    status: str = Field(description="Variant status: 'active' or 'inactive'")
    attribute_values: list[VariantAttributeValueResponse] = Field(
        description="Attribute-value pairs for this variant"
    )
    created_at: datetime = Field(description="When the variant was created (UTC)")
    updated_at: datetime = Field(description="When the variant was last updated (UTC)")


# --- images ------------------------------------------------------------------


class ProductImageResponse(BaseModel):
    id: uuid.UUID = Field(description="Image ID")
    product_id: uuid.UUID = Field(description="Product this image belongs to")
    url: str = Field(description="Cloudinary URL for the image")
    is_primary: bool = Field(description="Whether this is the primary product image")
    sort_order: int = Field(description="Display sort order (0-based)")
    created_at: datetime = Field(description="When the image was uploaded (UTC)")


# --- seller listings ---------------------------------------------------------


class SellerListingCreateRequest(BaseModel):
    variant_id: uuid.UUID = Field(description="ID of the catalog variant to list")
    price: float = Field(gt=0, description="Selling price (must be > 0)")
    stock: int = Field(ge=0, description="Available stock quantity")
    seller_sku: str | None = Field(
        default=None,
        max_length=100,
        description="Seller's own SKU code for this listing (optional)",
    )
    condition: Literal["new", "like_new", "used"] = Field(
        default="new", description="Item condition: 'new', 'like_new', or 'used'"
    )


class SellerListingUpdateRequest(BaseModel):
    price: float | None = Field(
        default=None, gt=0, description="New selling price (must be > 0)"
    )
    stock: int | None = Field(default=None, ge=0, description="New stock quantity")
    seller_sku: str | None = Field(
        default=None, max_length=100, description="Seller's own SKU code"
    )
    condition: Literal["new", "like_new", "used"] | None = Field(
        default=None, description="Item condition: 'new', 'like_new', or 'used'"
    )


class SellerListingUpdatePriceRequest(BaseModel):
    price: float = Field(gt=0, description="New selling price (must be > 0)")


class SellerListingUpdateStockRequest(BaseModel):
    stock: int = Field(ge=0, description="New stock quantity")


class RejectListingRequest(BaseModel):
    reason: str = Field(
        min_length=1, description="Admin reason for rejecting this listing"
    )


class SellerListingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Listing ID")
    seller_id: uuid.UUID = Field(description="Seller who owns this listing")
    variant_id: uuid.UUID = Field(description="Catalog variant being sold")
    price: float = Field(description="Current selling price")
    stock: int = Field(description="Available stock quantity")
    seller_sku: str | None = Field(description="Seller's own SKU code")
    condition: str = Field(description="Item condition: 'new', 'like_new', or 'used'")
    status: str = Field(
        description=(
            "Listing status: 'draft', 'pending_review', 'active', 'rejected', "
            "'suspended', 'out_of_stock', or 'archived'"
        )
    )
    rejection_reason: str | None = Field(
        description="Reason for rejection (set when status is 'rejected')"
    )
    created_at: datetime = Field(description="When the listing was created (UTC)")
    updated_at: datetime = Field(description="When the listing was last updated (UTC)")


class ListingImageResponse(BaseModel):
    id: uuid.UUID = Field(description="Image ID")
    listing_id: uuid.UUID = Field(description="Listing this image belongs to")
    url: str = Field(description="Cloudinary URL for the image")
    is_primary: bool = Field(description="Whether this is the primary listing image")
    sort_order: int = Field(description="Display sort order (0-based)")
    created_at: datetime = Field(description="When the image was uploaded (UTC)")
