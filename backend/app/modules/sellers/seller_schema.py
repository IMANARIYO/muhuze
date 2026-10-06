import uuid
from datetime import datetime
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.modules.auth.auth_constants import PHONE_PATTERN
from app.modules.sellers.seller_constants import (
    ADDRESS_PART_MAX_LENGTH,
    BUSINESS_DESCRIPTION_MAX_LENGTH,
    BUSINESS_NAME_MAX_LENGTH,
    BUSINESS_NAME_MIN_LENGTH,
    DEFAULT_COUNTRY_CODE,
    IDENTITY_DOCUMENT_NUMBER_MAX_LENGTH,
    IDENTITY_DOCUMENT_NUMBER_MIN_LENGTH,
    SEARCH_QUERY_MAX_LENGTH,
    STATUS_REASON_MAX_LENGTH,
    STATUS_REASON_MIN_LENGTH,
    STREET_ADDRESS_MAX_LENGTH,
    IdentityDocumentType,
    LocationSource,
    SellerDocumentType,
    SellerStatus,
)

BusinessName = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=BUSINESS_NAME_MIN_LENGTH,
        max_length=BUSINESS_NAME_MAX_LENGTH,
    ),
]
BusinessDescription = Annotated[
    str, StringConstraints(strip_whitespace=True, max_length=BUSINESS_DESCRIPTION_MAX_LENGTH)
]
BusinessPhone = Annotated[
    str, Field(pattern=PHONE_PATTERN, description="E.164 format, e.g. +2507XXXXXXXX")
]
IdentityDocumentNumber = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=IDENTITY_DOCUMENT_NUMBER_MIN_LENGTH,
        max_length=IDENTITY_DOCUMENT_NUMBER_MAX_LENGTH,
    ),
]
RequiredAddressPart = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=ADDRESS_PART_MAX_LENGTH),
]
OptionalAddressPart = Annotated[
    str, StringConstraints(strip_whitespace=True, max_length=ADDRESS_PART_MAX_LENGTH)
]


class SellerLocation(BaseModel):
    """Where the business is. The address is required; coordinates are optional."""

    model_config = ConfigDict(from_attributes=True)

    country_code: Annotated[str, StringConstraints(to_upper=True, pattern=r"^[A-Za-z]{2}$")] = (
        Field(default=DEFAULT_COUNTRY_CODE, description="ISO 3166-1 alpha-2")
    )
    province: RequiredAddressPart
    district: RequiredAddressPart
    sector: RequiredAddressPart
    cell: OptionalAddressPart | None = None
    village: OptionalAddressPart | None = None
    street_address: (
        Annotated[
            str, StringConstraints(strip_whitespace=True, max_length=STREET_ADDRESS_MAX_LENGTH)
        ]
        | None
    ) = Field(default=None, description="Street, building, landmark")
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    accuracy_m: int | None = Field(
        default=None, ge=0, description="Accuracy in metres reported by the device"
    )
    source: LocationSource | None = Field(
        default=None,
        description="How the coordinates were captured: read from the device, or a manual pin",
    )

    @model_validator(mode="after")
    def _coordinates_are_complete(self) -> Self:
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude and longitude must be sent together")
        if self.latitude is None and (self.source is not None or self.accuracy_m is not None):
            raise ValueError("source and accuracy_m need latitude and longitude")
        if self.latitude is not None and self.source is None:
            raise ValueError("source is required when coordinates are sent")
        return self


class SellerApplicationRequest(BaseModel):
    business_name: BusinessName = Field(description="The shop name buyers will see; unique")
    business_description: BusinessDescription | None = None
    business_phone: BusinessPhone
    identity_document_type: IdentityDocumentType
    identity_document_number: IdentityDocumentNumber = Field(
        description="As printed on the identity document"
    )
    location: SellerLocation


class SellerUpdateRequest(BaseModel):
    """Only the fields that are sent are changed. `location` is replaced as a whole."""

    business_name: BusinessName | None = None
    business_description: BusinessDescription | None = None
    business_phone: BusinessPhone | None = None
    identity_document_type: IdentityDocumentType | None = None
    identity_document_number: IdentityDocumentNumber | None = None
    location: SellerLocation | None = None

    @model_validator(mode="after")
    def _required_fields_cannot_be_cleared(self) -> Self:
        for field in self.model_fields_set - {"business_description"}:
            if getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


class SellerDocumentResponse(BaseModel):
    document_type: SellerDocumentType
    original_filename: str | None
    mime_type: str
    file_size: int = Field(description="Bytes")
    uploaded_at: datetime


class SellerResponse(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    business_name: str
    business_description: str | None
    business_phone: str
    identity_document_type: IdentityDocumentType
    identity_document_number: str = Field(
        description="Sensitive: returned to the owner and to reviewing staff only"
    )
    location: SellerLocation
    status: SellerStatus
    status_reason: str | None = Field(description="Why it was rejected or suspended")
    submitted_at: datetime | None
    reviewed_by_account_id: uuid.UUID | None
    reviewed_at: datetime | None
    approved_at: datetime | None
    created_at: datetime
    documents: list[SellerDocumentResponse]
    missing_documents: list[SellerDocumentType] = Field(
        description="Required documents not uploaded yet; must be empty to submit"
    )


class SellerSummaryResponse(BaseModel):
    """One row of the staff list. No identity details."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    business_name: str
    business_phone: str
    district: str
    status: SellerStatus
    submitted_at: datetime | None
    created_at: datetime


SellerSort = Literal[
    "created_at",
    "-created_at",
    "submitted_at",
    "-submitted_at",
    "business_name",
    "-business_name",
]


class SellerListFilters(BaseModel):
    status: SellerStatus | None = Field(default=None, description="Only sellers in this status")
    q: str | None = Field(
        default=None,
        min_length=1,
        max_length=SEARCH_QUERY_MAX_LENGTH,
        description="Search in the business name (contains, case-insensitive)",
    )
    sort: SellerSort = Field(
        default="-created_at", description="Field to sort by; prefix with - for descending"
    )


class StatusReasonRequest(BaseModel):
    reason: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=STATUS_REASON_MIN_LENGTH,
            max_length=STATUS_REASON_MAX_LENGTH,
        ),
    ] = Field(description="Shown to the seller")


class SellerStatusHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    from_status: SellerStatus | None
    to_status: SellerStatus
    reason: str | None
    changed_by_account_id: uuid.UUID | None
    created_at: datetime


class DocumentUrlResponse(BaseModel):
    url: str = Field(description="A private link to the file. Do not store it: it expires")
    expires_in: int = Field(description="Seconds until the link stops working")
