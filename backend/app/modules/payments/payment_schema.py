import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.modules.auth.auth_constants import PHONE_PATTERN
from app.modules.payments.payment_constants import (
    ACCOUNT_REFERENCE_MAX_LENGTH,
    INSTRUCTIONS_MAX_LENGTH,
    PAYER_NAME_MAX_LENGTH,
    PROVIDER_MAX_LENGTH,
    REASON_MAX_LENGTH,
    REASON_MIN_LENGTH,
    REFERENCE_MAX_LENGTH,
    REFERENCE_MIN_LENGTH,
    REGISTERED_NAME_MAX_LENGTH,
    SEARCH_QUERY_MAX_LENGTH,
    PaymentMethod,
    PaymentStatus,
)


def _text(max_length: int, *, min_length: int = 1) -> type[str]:
    return Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=min_length, max_length=max_length),
    ]


Provider = _text(PROVIDER_MAX_LENGTH)
AccountReference = _text(ACCOUNT_REFERENCE_MAX_LENGTH)
RegisteredName = _text(REGISTERED_NAME_MAX_LENGTH)
Instructions = Annotated[
    str, StringConstraints(strip_whitespace=True, max_length=INSTRUCTIONS_MAX_LENGTH)
]


def _reject_nulls(model: BaseModel, nullable: set[str]) -> None:
    for field in model.model_fields_set - nullable:
        if getattr(model, field) is None:
            raise ValueError(f"{field} cannot be null")


# ── Destinations ─────────────────────────────────────────────────────────


class PaymentDestinationResponse(BaseModel):
    """The full record, for staff."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    method: PaymentMethod
    provider: str
    account_reference: str
    registered_name: str
    currency: str
    instructions: str | None
    is_active: bool
    is_default: bool
    created_at: datetime


class PaymentDestinationCreateRequest(BaseModel):
    method: PaymentMethod
    provider: Provider = Field(description="The mobile-money network or bank, as buyers know it")
    account_reference: AccountReference = Field(
        description="The phone number, merchant code, or bank account number"
    )
    registered_name: RegisteredName = Field(
        description="The name the buyer sees when paying, so they know it is MUHUZE"
    )
    instructions: Instructions | None = None
    is_default: bool = Field(default=False, description="Show it first to buyers")


class PaymentDestinationUpdateRequest(BaseModel):
    """Only the fields that are sent are changed. Past payments keep the
    details they were made to."""

    method: PaymentMethod | None = None
    provider: Provider | None = None
    account_reference: AccountReference | None = None
    registered_name: RegisteredName | None = None
    instructions: Instructions | None = None

    @model_validator(mode="after")
    def _no_nulls(self) -> Self:
        _reject_nulls(self, nullable={"instructions"})
        return self


class PayToResponse(BaseModel):
    """What a buyer needs to pay, and nothing more (README §12.3)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    method: PaymentMethod
    provider: str
    account_reference: str
    registered_name: str
    instructions: str | None
    is_default: bool


# ── Payments ─────────────────────────────────────────────────────────────


class PaymentSubmitRequest(BaseModel):
    destination_id: uuid.UUID = Field(description="The account you paid, from the instructions")
    reference: _text(REFERENCE_MAX_LENGTH, min_length=REFERENCE_MIN_LENGTH) = Field(
        description="The transaction id from your mobile-money or bank message"
    )
    payer_name: _text(PAYER_NAME_MAX_LENGTH) | None = Field(
        default=None, description="The name on the account you paid from"
    )
    payer_phone: str | None = Field(
        default=None, pattern=PHONE_PATTERN, description="The number you paid from, E.164"
    )

    @model_validator(mode="after")
    def _who_paid(self) -> Self:
        if self.payer_name is None and self.payer_phone is None:
            raise ValueError("send payer_name or payer_phone, so the payment can be matched")
        return self


class PaymentResponse(BaseModel):
    """A payment attempt, as the buyer sees it."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_id: uuid.UUID
    status: PaymentStatus
    amount: Decimal
    currency: str
    reference: str
    destination_method: PaymentMethod
    destination_provider: str
    destination_account_reference: str
    destination_registered_name: str
    rejection_reason: str | None
    paid_at: datetime | None
    created_at: datetime


class StaffPaymentResponse(PaymentResponse):
    """Everything staff need to match it against MUHUZE's statement."""

    order_number: str
    payer_account_id: uuid.UUID
    payer_name: str | None
    payer_phone: str | None
    channel: str
    verified_by_account_id: uuid.UUID | None
    verified_at: datetime | None


class PaymentInstructionsResponse(BaseModel):
    order_id: uuid.UUID
    order_number: str
    amount: Decimal = Field(description="Pay exactly this")
    currency: str
    can_pay: bool = Field(
        description="True when a payment can be submitted now: the order is unpaid, not "
        "cancelled, and has no payment waiting to be verified"
    )
    pay_to: list[PayToResponse] = Field(
        description="MUHUZE's accounts, default first. Empty unless the order awaits payment"
    )
    attempts: list[PaymentResponse] = Field(description="Payments submitted so far, newest first")


class ReasonRequest(BaseModel):
    reason: _text(REASON_MAX_LENGTH, min_length=REASON_MIN_LENGTH) = Field(
        description="Shown to the buyer"
    )


class StaffPaymentFilters(BaseModel):
    status: PaymentStatus | None = Field(
        default=None, description="`awaiting_verification` is the queue of payments to check"
    )
    q: str | None = Field(
        default=None,
        min_length=1,
        max_length=SEARCH_QUERY_MAX_LENGTH,
        description="Search the transaction reference or order number (contains)",
    )
