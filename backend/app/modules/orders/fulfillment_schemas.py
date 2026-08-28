import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ShipmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Shipment ID")
    carrier: str | None = Field(description="Carrier name")
    tracking_number: str | None = Field(description="Tracking number")
    status: str = Field(description="shipped | delivered")
    shipped_at: datetime | None = Field(description="When dispatched (UTC)")
    delivered_at: datetime | None = Field(description="When delivered (UTC)")
    notes: str | None = Field(description="Delivery notes")


class SellerOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Seller order ID")
    order_id: uuid.UUID = Field(description="The buyer order this is a slice of")
    seller_id: uuid.UUID = Field(description="Which seller fulfills it")
    status: str = Field(
        description="pending | accepted | rejected | shipped | delivered | cancelled"
    )
    rejected_reason: str | None = Field(description="Why rejected (if rejected)")
    accepted_at: datetime | None = Field(description="When accepted (UTC)")
    shipped_at: datetime | None = Field(description="When shipped (UTC)")
    delivered_at: datetime | None = Field(description="When delivered (UTC)")
    created_at: datetime = Field(description="When created (UTC)")
    updated_at: datetime = Field(description="When last updated (UTC)")
    shipment: ShipmentResponse | None = Field(default=None, description="Active shipment, if any")


class RejectSellerOrderRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500, description="Why the seller cannot fulfill")


class ShipSellerOrderRequest(BaseModel):
    carrier: str | None = Field(default=None, max_length=60, description="Carrier name")
    tracking_number: str | None = Field(default=None, max_length=255, description="Tracking number")
    notes: str | None = Field(default=None, max_length=500, description="Delivery notes")
