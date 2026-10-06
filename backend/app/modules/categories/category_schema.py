import uuid
from datetime import datetime
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.modules.categories.category_constants import (
    ATTRIBUTE_NAME_MAX_LENGTH,
    ATTRIBUTE_UNIT_MAX_LENGTH,
    CATEGORY_DESCRIPTION_MAX_LENGTH,
    CATEGORY_NAME_MAX_LENGTH,
    OPTION_DATA_TYPES,
    OPTION_VALUE_MAX_LENGTH,
    SEARCH_QUERY_MAX_LENGTH,
    AttributeDataType,
)

CategoryName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=CATEGORY_NAME_MAX_LENGTH),
]
CategoryDescription = Annotated[
    str, StringConstraints(strip_whitespace=True, max_length=CATEGORY_DESCRIPTION_MAX_LENGTH)
]
AttributeName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=ATTRIBUTE_NAME_MAX_LENGTH),
]
AttributeUnit = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=ATTRIBUTE_UNIT_MAX_LENGTH),
]
OptionValue = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=OPTION_VALUE_MAX_LENGTH),
]
SortOrder = Annotated[int, Field(ge=0, le=100_000, description="Lower numbers are shown first")]


def _reject_nulls(model: BaseModel, nullable: set[str]) -> None:
    """In an update, a field that is sent must have a value unless it is one
    that can genuinely be cleared."""
    for field in model.model_fields_set - nullable:
        if getattr(model, field) is None:
            raise ValueError(f"{field} cannot be null")


# ── Options ──────────────────────────────────────────────────────────────


class OptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    value: str
    sort_order: int
    is_active: bool


class OptionCreateRequest(BaseModel):
    value: OptionValue
    sort_order: SortOrder | None = Field(default=None, description="Omit to add it at the end")


class OptionUpdateRequest(BaseModel):
    """Only the fields that are sent are changed."""

    value: OptionValue | None = None
    sort_order: SortOrder | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def _no_nulls(self) -> Self:
        _reject_nulls(self, nullable=set())
        return self


# ── Attributes ───────────────────────────────────────────────────────────


class AttributeResponse(BaseModel):
    id: uuid.UUID
    code: str = Field(description="Stable key for this attribute; never changes")
    name: str
    data_type: AttributeDataType
    unit: str | None
    is_required: bool
    is_filterable: bool
    sort_order: int
    is_active: bool
    options: list[OptionResponse] = Field(description="Allowed values, for select types")


class AttributeCreateRequest(BaseModel):
    name: AttributeName = Field(description="What people see, e.g. Storage")
    data_type: AttributeDataType = Field(description="Cannot be changed later")
    unit: AttributeUnit | None = Field(default=None, description="For numbers: GB, kg, cm")
    is_required: bool = False
    is_filterable: bool = False
    sort_order: SortOrder = 0
    options: list[OptionValue] = Field(
        default_factory=list,
        max_length=200,
        description="Allowed values, for select and multi_select only",
    )

    @model_validator(mode="after")
    def _fields_fit_the_type(self) -> Self:
        if self.options and self.data_type not in OPTION_DATA_TYPES:
            raise ValueError("options are only for select and multi_select attributes")
        if self.unit is not None and self.data_type != AttributeDataType.NUMBER:
            raise ValueError("unit is only for number attributes")
        lowered = [option.lower() for option in self.options]
        if len(lowered) != len(set(lowered)):
            raise ValueError("options must not repeat")
        return self


class AttributeUpdateRequest(BaseModel):
    """Only the fields that are sent are changed. The type cannot be changed."""

    name: AttributeName | None = None
    unit: AttributeUnit | None = None
    is_required: bool | None = None
    is_filterable: bool | None = None
    sort_order: SortOrder | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def _no_nulls(self) -> Self:
        _reject_nulls(self, nullable={"unit"})
        return self


# ── Categories ───────────────────────────────────────────────────────────


class CategorySummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    seller_id: uuid.UUID
    name: str
    slug: str
    description: str | None
    sort_order: int
    is_active: bool
    hidden_by_staff_at: datetime | None = Field(
        description="Set when MUHUZE hid the category; the seller cannot reactivate it"
    )
    created_at: datetime


class CategoryResponse(CategorySummaryResponse):
    attributes: list[AttributeResponse]


class CategoryCreateRequest(BaseModel):
    name: CategoryName = Field(description="Unique within your shop")
    description: CategoryDescription | None = None
    sort_order: SortOrder = 0


class CategoryUpdateRequest(BaseModel):
    """Only the fields that are sent are changed."""

    name: CategoryName | None = None
    description: CategoryDescription | None = None
    sort_order: SortOrder | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def _no_nulls(self) -> Self:
        _reject_nulls(self, nullable={"description"})
        return self


class OwnCategoryFilters(BaseModel):
    is_active: bool | None = Field(default=None, description="Only active, or only inactive")
    q: str | None = Field(
        default=None,
        min_length=1,
        max_length=SEARCH_QUERY_MAX_LENGTH,
        description="Search in the category name (contains, case-insensitive)",
    )


class StaffCategoryFilters(OwnCategoryFilters):
    seller_id: uuid.UUID | None = Field(default=None, description="Only this shop's categories")
