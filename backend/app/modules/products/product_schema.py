import uuid
from datetime import datetime, time
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
    SERVICE_AREAS_MAX,
    SERVICE_DURATION_MAX_MINUTES,
    SERVICE_MIN_NOTICE_MAX_HOURS,
    ProductKind,
    ProductStatus,
    ServiceLocation,
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
District = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class ServiceHoursInput(BaseModel):
    weekday: int = Field(ge=1, le=7, description="1 = Monday … 7 = Sunday")
    opens_at: time = Field(description="Local time (Rwanda), e.g. 08:00")
    closes_at: time = Field(description="Local time; a request must START before this")

    @model_validator(mode="after")
    def _opens_before_closing(self) -> Self:
        if self.opens_at >= self.closes_at:
            raise ValueError("opens_at must be before closes_at")
        return self


class ServiceDetailsInput(BaseModel):
    """What only a service has (README §7.5, V15–V18). A draft may leave any
    of it out; publishing needs it all. On an update only the fields sent
    change, and a list sent replaces the old one."""

    location: ServiceLocation | None = Field(
        default=None,
        description="`at_customer` (you go to the buyer), `at_provider` (the buyer comes "
        "to your shop's address), or `online`",
    )
    duration_minutes: int | None = Field(
        default=None, ge=1, le=SERVICE_DURATION_MAX_MINUTES, description="How long the job takes"
    )
    min_notice_hours: int | None = Field(
        default=None,
        ge=0,
        le=SERVICE_MIN_NOTICE_MAX_HOURS,
        description="How many hours ahead a request must be for; 0 = any future time",
    )
    areas: list[District] | None = Field(
        default=None,
        max_length=SERVICE_AREAS_MAX,
        description="The districts you work in. Only for `at_customer`, which needs at least one",
    )
    hours: list[ServiceHoursInput] | None = Field(
        default=None,
        max_length=7,
        description="When a job can start, at most one range per weekday; a missing day is off",
    )

    @model_validator(mode="after")
    def _no_repeats(self) -> Self:
        if self.areas is not None and len({a.casefold() for a in self.areas}) != len(self.areas):
            raise ValueError("areas must not repeat a district")
        if self.hours is not None and len({h.weekday for h in self.hours}) != len(self.hours):
            raise ValueError("hours must have at most one range per weekday")
        return self


# ── Requests ─────────────────────────────────────────────────────────────


class ProductCreateRequest(BaseModel):
    kind: ProductKind = Field(
        default=ProductKind.PRODUCT,
        description=(
            "`product` (bought through checkout) or `service` (booked by request). "
            "Cannot be changed later."
        ),
    )
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
    service: ServiceDetailsInput | None = Field(
        default=None, description="Only for a service: where, how long, notice, areas, hours"
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
    service: ServiceDetailsInput | None = Field(
        default=None, description="Only for a service. Only the fields sent are changed"
    )

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
    kind: ProductKind
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


class ServiceHoursResponse(BaseModel):
    weekday: int = Field(description="1 = Monday … 7 = Sunday")
    opens_at: time
    closes_at: time


class ServiceDetailsResponse(BaseModel):
    """A service's details. Any may be null while it is a draft."""

    location: ServiceLocation | None
    duration_minutes: int | None
    min_notice_hours: int | None
    areas: list[str] = Field(description="Districts covered; only for `at_customer`")
    hours: list[ServiceHoursResponse] = Field(description="Local time (Rwanda), Monday first")


class ProductResponse(ProductSummaryResponse):
    description: str | None
    images: list[ProductImageResponse]
    attributes: list[ProductAttributeValueResponse]
    service: ServiceDetailsResponse | None = Field(default=None, description="Null for goods")


class OwnProductResponse(ProductResponse):
    publish_blockers: list[str] = Field(
        description="What still stops this product being published; empty when it is ready"
    )


class ShopSummaryResponse(BaseModel):
    id: uuid.UUID
    name: str


class ProviderAreaResponse(BaseModel):
    """Where an `at_provider` service is done, roughly. The street address is
    on the buyer's order once paid (README §7.5, V15)."""

    province: str
    district: str
    sector: str


class PublicProductResponse(ProductResponse):
    shop: ShopSummaryResponse
    contact_phone: str | None = Field(
        default=None,
        description=(
            "The provider's business phone. Only for a service, and only while the "
            "provider has a subscription in force; null otherwise (README §7.5)"
        ),
    )
    provider_area: ProviderAreaResponse | None = Field(
        default=None, description="Only for an `at_provider` service: where the shop is"
    )


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
    kind: ProductKind | None = Field(default=None, description="Only products or only services")
    status: ProductStatus | None = None
    sort: OwnProductSort = Field(default="-created_at", description="Prefix - for descending")


class StaffProductFilters(OwnProductFilters):
    seller_id: uuid.UUID | None = Field(default=None, description="Only this shop")


class PublicProductFilters(_ProductSearch):
    # Defaults to goods, so a storefront that only knows checkout never lists
    # services by surprise.
    kind: ProductKind = Field(
        default=ProductKind.PRODUCT, description="`product` (default) or `service`"
    )
    seller_id: uuid.UUID | None = Field(default=None, description="Only this shop")
    district: District | None = Field(
        default=None,
        description="Services only: those a buyer in this district can get (case-insensitive): "
        "done there, at a shop there, or online",
    )
    min_price: Decimal | None = Field(default=None, ge=0)
    max_price: Decimal | None = Field(default=None, ge=0)
    sort: PublicProductSort = Field(default="-published_at", description="Prefix - for descending")
