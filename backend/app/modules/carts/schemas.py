import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AddCartItemRequest(BaseModel):
    listing_id: uuid.UUID = Field(description="The seller listing to add")
    quantity: int = Field(default=1, ge=1, description="How many to add (>=1)")


class UpdateCartItemRequest(BaseModel):
    quantity: int = Field(ge=1, description="New quantity (>=1)")


class CartItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Cart line ID")
    listing_id: uuid.UUID = Field(description="The seller listing in the cart")
    seller_id: uuid.UUID = Field(description="The seller offering this line")
    seller_name: str = Field(description="The seller's business/shop name")
    product_id: uuid.UUID = Field(description="The product (SPU) this line belongs to")
    product_name: str = Field(description="Product name (snapshot for display)")
    product_image: str | None = Field(
        description="Primary product image URL (public, CDN-served) — null if the product has no images"
    )
    variant_name: str | None = Field(description="Variant label, e.g. 128GB / Black")
    unit_price: float = Field(description="Current listing price at time of read")
    condition: str = Field(description="Item condition: 'new', 'like_new', or 'used'")
    stock: int = Field(description="Current available stock at time of read")
    quantity: int = Field(description="Quantity in cart")
    subtotal: float = Field(description="unit_price * quantity")
    created_at: datetime = Field(description="When added (UTC)")
    updated_at: datetime = Field(description="When last updated (UTC)")


class CartResponse(BaseModel):
    items: list[CartItemResponse] = Field(description="The cart lines")
    item_count: int = Field(description="Total number of distinct lines")
    total: float = Field(description="Sum of all line subtotals (gross)")
