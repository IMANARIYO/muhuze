import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ShippingAddressRequest(BaseModel):
    label: str | None = Field(default=None, max_length=50, description="Home / Work / Other")
    recipient_name: str = Field(min_length=1, max_length=150, description="Who to hand it to")
    phone: str = Field(min_length=1, max_length=20, description="Delivery recipient phone")
    country: str = Field(default="Rwanda", max_length=60, description="Country")
    province: str | None = Field(default=None, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    sector: str | None = Field(default=None, max_length=100)
    cell: str | None = Field(default=None, max_length=100)
    village: str | None = Field(default=None, max_length=100)
    address_line: str | None = Field(default=None, max_length=255, description="Street / building / landmarks")
    delivery_instructions: str | None = Field(default=None, max_length=255, description="e.g. call on arrival")
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    is_default: bool = Field(default=False, description="Whether this is the default address")


class ShippingAddressUpdateRequest(BaseModel):
    label: str | None = Field(default=None, max_length=50)
    recipient_name: str | None = Field(default=None, min_length=1, max_length=150)
    phone: str | None = Field(default=None, min_length=1, max_length=20)
    country: str | None = Field(default=None, max_length=60)
    province: str | None = Field(default=None, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    sector: str | None = Field(default=None, max_length=100)
    cell: str | None = Field(default=None, max_length=100)
    village: str | None = Field(default=None, max_length=100)
    address_line: str | None = Field(default=None, max_length=255)
    delivery_instructions: str | None = Field(default=None, max_length=255)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    is_default: bool | None = Field(default=None)


class ShippingAddressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Address ID")
    label: str | None = Field(description="Home / Work / Other")
    recipient_name: str = Field(description="Who to hand it to")
    phone: str = Field(description="Delivery recipient phone")
    country: str = Field(description="Country")
    province: str | None = Field(description="Province")
    district: str | None = Field(description="District")
    sector: str | None = Field(description="Sector")
    cell: str | None = Field(description="Cell")
    village: str | None = Field(description="Village")
    address_line: str | None = Field(description="Street / building / landmarks")
    delivery_instructions: str | None = Field(description="Delivery instructions")
    latitude: float | None = Field(description="Latitude")
    longitude: float | None = Field(description="Longitude")
    is_default: bool = Field(description="Whether this is the default address")
    created_at: datetime = Field(description="When created (UTC)")
    updated_at: datetime = Field(description="When last updated (UTC)")
