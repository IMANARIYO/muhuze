import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RevenueLine(BaseModel):
    """One seller's revenue split inside a paid order."""

    id: uuid.UUID = Field(description="Revenue transaction ID")
    seller_id: uuid.UUID = Field(description="The seller")
    amount: float = Field(description="Gross from this seller")
    revenue_rate: float = Field(description="7% premium / 12% basic snapshot")
    commission_amount: float = Field(description="MUHUZE's cut")
    seller_earning: float = Field(description="Net to seller")
    referral_eligible: bool = Field(description="Whether referral commission is eligible")
    status: str = Field(description="held until buyer confirms receipt, then released")
    released_at: datetime | None = Field(description="When MUHUZE released the earning")


class RevenueTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Revenue transaction ID")
    order_id: uuid.UUID = Field(description="The order")
    payment_id: uuid.UUID = Field(description="The payment that cleared")
    seller_id: uuid.UUID = Field(description="The seller")
    amount: float = Field(description="Gross from this seller")
    revenue_rate: float = Field(description="Rate snapshot")
    commission_amount: float = Field(description="MUHUZE's cut")
    seller_earning: float = Field(description="Net to seller")
    currency: str = Field(description="Currency")
    referral_eligible: bool = Field(description="Referral eligibility")
    status: str = Field(description="held | released")
    released_at: datetime | None = Field(description="When released (UTC)")
    created_at: datetime = Field(description="When recorded (UTC)")
    updated_at: datetime = Field(description="When last updated (UTC)")


class RevenueSummaryResponse(BaseModel):
    total_gross: float = Field(description="Total gross across sellers")
    total_commission: float = Field(description="Total MUHUZE revenue")
    total_seller_earning: float = Field(description="Total net to sellers")
