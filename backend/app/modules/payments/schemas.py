import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CreatePaymentRequest(BaseModel):
    """Initiate a mobile-money payment for an order.

    The caller supplies the Airtel Money wallet to charge (`momo_phone`) and
    the Airtel line the payment is made from (`airtel_phone`). The stub
    gateway immediately returns a `request_reference` stored as
    `provider_ref`; the provider callback (`POST /payments/{id}/paid`)
    clears the money and triggers revenue derivation.
    """

    order_id: uuid.UUID = Field(description="The order to pay for")
    momo_phone: str = Field(
        min_length=1, max_length=20, description="Buyer's Airtel Money wallet number to charge"
    )
    airtel_phone: str = Field(
        min_length=1, max_length=20, description="Airtel line the payment is sent from"
    )
    method: str | None = Field(
        default="airtel_money", max_length=30, description="Payment method"
    )


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Payment ID")
    order_id: uuid.UUID = Field(description="The order being paid")
    status: str = Field(description="pending | paid | failed | refunded | partially_refunded")
    amount: float = Field(description="Amount paid (equals order total)")
    currency: str = Field(description="Billing currency")
    momo_phone: str | None = Field(description="Airtel Money wallet charged")
    airtel_phone: str | None = Field(description="Airtel line the payment was sent from")
    method: str | None = Field(description="Payment method")
    provider_ref: str | None = Field(description="Gateway request reference")
    paid_at: datetime | None = Field(description="When the payment cleared (UTC)")
    created_at: datetime = Field(description="When created (UTC)")
    updated_at: datetime = Field(description="When last updated (UTC)")


class PaidPaymentResponse(PaymentResponse):
    revenue: int = Field(description="Number of revenue_transactions created for this payment")
