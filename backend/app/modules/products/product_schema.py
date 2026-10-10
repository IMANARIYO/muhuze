import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.modules.categories.category_constants import AttributeDataType
from app.modules.products.product_constants import (
    PRICE_DECIMAL_PLACES,
    PRICE_MAX_DIGITS,
    PRODUCT_DESCRIPTION_MAX_LENGTH,
    PRODUCT_NAME_MAX_LENGTH,
    SEARCH_QUERY_MAX_LENGTH,
    ProductStatus,
)

ProductName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=PRODUCT_NAME_MAX_LENGTH),
]
ProductDescription = Annotated[
    str, StringConstraints(strip_whitespace=True, max_length=PRODUCT_DESCRIPTION_MAX_LENGTH)
]
# Decimal, never float. Serialized as a string ("25000.00").
Price = Annotated[
    Decimal,
    Field(
        gt=0,
        max_digits=PRICE_MAX_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        description="Price of one unit, as a decimal string",
    ),
]
# Attribute values keyed by the attribute's `code`. The shape of each value
# depends on the attribute's type, so it is checked in the service against
# the category: text → string, number → number, boolean → true/false,
# select → option id, multi_select → list of option ids. null clears a value.
AttributeValuesInput = dict[str, Any]


# ── Requests ─────────────────────────────────────────────────────────────


class ProductCreateRequest(BaseModel):
    name: ProductName
    description: ProductDescription | None = None
    price: Price
    category_id: uuid.UUID = Field(description="One of your own categories")
    attributes: AttributeValuesInput = Field(
        default_factory=dict,
        description=(
            "Values keyed by attribute code: text → string, number → number, "
            "boolean → true/false, select → option id, multi_select → list of option ids"
        ),
    )


class ProductUpdateRequest(BaseModel):
    """Only the fields that are sent are changed. In `attributes`, only the
    codes that are sent are changed; null clears one."""

    name: ProductName | None = None
    description: ProductDescription | None = None
    price: Price | None = None
    category_id: uuid.UUID | None = Field(
        default=None, description="Moving to another category drops the old attribute values"
    )
    attributes: AttributeValuesInput | None = None

    @model_validator(mode="after")
    def _required_fields_cannot_be_cleared(self) -> Self:
        for field in self.model_fields_set - {"description"}:
            if getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


class ImageOrderRequest(BaseModel):
    image_ids: list[uuid.UUID] = Field(
        min_length=1, description="Every image of the product, in the order wanted; first = main"
    )


# ── Responses ────────────────────────────────────────────────────────────


class ProductImageResponse(BaseModel):
    id: uuid.UUID
    url: str
    width: int | None
    height: int | None
    sort_order: int


class OptionValueResponse(BaseModel):
    id: uuid.UUID
    value: str


class ProductAttributeValueResponse(BaseModel):
    code: str
    name: str
    data_type: AttributeDataType
    unit: str | None
    value: bool | int | float | str | OptionValueResponse | list[OptionValueResponse] = Field(
        description="A string, number, boolean, one option, or a list of options, by data_type"
    )


class ProductSummaryResponse(BaseModel):
    """One row of a product list."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    seller_id: uuid.UUID
    category_id: uuid.UUID
    name: str
    slug: str
    price: Decimal
    currency: str
    status: ProductStatus
    main_image_url: str | None = None
    published_at: datetime | None
    hidden_by_staff_at: datetime | None = Field(
        description="Set when MUHUZE hid the product; buyers never see hidden products"
    )
    created_at: datetime


class ProductResponse(ProductSummaryResponse):
    description: str | None
    images: list[ProductImageResponse]
    attributes: list[ProductAttributeValueResponse]


class OwnProductResponse(ProductResponse):
    publish_blockers: list[str] = Field(
        description="What still stops this product being published; empty when it is ready"
    )


class ShopSummaryResponse(BaseModel):
    id: uuid.UUID
    name: str


class PublicProductResponse(ProductResponse):
    shop: ShopSummaryResponse


# ── List filters ─────────────────────────────────────────────────────────

OwnProductSort = Literal["created_at", "-created_at", "price", "-price", "name", "-name"]
PublicProductSort = Literal["published_at", "-published_at", "price", "-price", "name", "-name"]


class _ProductSearch(BaseModel):
    category_id: uuid.UUID | None = Field(default=None, description="Only this category")
    q: str | None = Field(
        default=None,
        min_length=1,
        max_length=SEARCH_QUERY_MAX_LENGTH,
        description="Search in the product name (contains, case-insensitive)",
    )


class OwnProductFilters(_ProductSearch):
    status: ProductStatus | None = None
    sort: OwnProductSort = Field(default="-created_at", description="Prefix - for descending")


class StaffProductFilters(OwnProductFilters):
    seller_id: uuid.UUID | None = Field(default=None, description="Only this shop")


class PublicProductFilters(_ProductSearch):
    seller_id: uuid.UUID | None = Field(default=None, description="Only this shop")
    min_price: Decimal | None = Field(default=None, ge=0)
    max_price: Decimal | None = Field(default=None, ge=0)
    sort: PublicProductSort = Field(default="-published_at", description="Prefix - for descending")
