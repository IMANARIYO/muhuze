import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.modules.withdrawals.withdrawal_constants import (
    ACCOUNT_NAME_MAX_LENGTH,
    ACCOUNT_NUMBER_MAX_LENGTH,
    PAYOUT_REFERENCE_MAX_LENGTH,
    PROVIDER_MAX_LENGTH,
    REASON_MAX_LENGTH,
    REASON_MIN_LENGTH,
    PayoutDestinationType,
    WithdrawalStatus,
)


def _text(max_length: int, *, min_length: int = 1) -> type[str]:
    return Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=min_length, max_length=max_length),
    ]


Provider = _text(PROVIDER_MAX_LENGTH)
AccountNumber = _text(ACCOUNT_NUMBER_MAX_LENGTH)
AccountName = _text(ACCOUNT_NAME_MAX_LENGTH)


def _reject_nulls(model: BaseModel, nullable: set[str]) -> None:
    for field in model.model_fields_set - nullable:
        if getattr(model, field) is None:
            raise ValueError(f"{field} cannot be null")


# ── Payout destinations ──────────────────────────────────────────────────


class PayoutDestinationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    seller_id: uuid.UUID
    type: PayoutDestinationType
    provider: str
    account_number: str
    account_name: str
    is_active: bool
    created_at: datetime


class PayoutDestinationCreateRequest(BaseModel):
    type: PayoutDestinationType = Field(description="`mobile_money` or `bank`")
    provider: Provider = Field(description="The mobile-money network or the bank")
    account_number: AccountNumber = Field(description="The phone number or bank account")
    account_name: AccountName = Field(description="The name registered on that account")


class PayoutDestinationUpdateRequest(BaseModel):
    """Only the fields that are sent are changed. Past withdrawals keep the
    details they were paid to."""

    type: PayoutDestinationType | None = None
    provider: Provider | None = None
    account_number: AccountNumber | None = None
    account_name: AccountName | None = None

    @model_validator(mode="after")
    def _no_nulls(self) -> Self:
        _reject_nulls(self, nullable=set())
        return self


# ── Withdrawals ──────────────────────────────────────────────────────────


class WithdrawalRequest(BaseModel):
    amount: Decimal = Field(
        gt=0, max_digits=16, decimal_places=2, description="How much of your available balance"
    )
    payout_destination_id: uuid.UUID = Field(
        description="Where to send it, from your saved accounts"
    )


class WithdrawalResponse(BaseModel):
    """A withdrawal, as its seller sees it."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    seller_id: uuid.UUID
    amount: Decimal
    currency: str
    status: WithdrawalStatus
    destination_type: PayoutDestinationType
    destination_provider: str
    destination_account_number: str
    destination_account_name: str
    reason: str | None = Field(
        default=None, description="Why staff rejected or failed it; null otherwise"
    )
    payout_reference: str | None = Field(
        default=None, description="The external id of the payout, when staff record one"
    )
    created_at: datetime
    completed_at: datetime | None


class StaffWithdrawalResponse(WithdrawalResponse):
    """Everything staff need to review it."""

    reviewed_by_account_id: uuid.UUID | None
    reviewed_at: datetime | None
    updated_at: datetime


class ReasonRequest(BaseModel):
    reason: _text(REASON_MAX_LENGTH, min_length=REASON_MIN_LENGTH) = Field(
        description="Shown to the seller"
    )


class CompleteRequest(BaseModel):
    payout_reference: _text(PAYOUT_REFERENCE_MAX_LENGTH) | None = Field(
        default=None, description="The transaction id of the payout you made by hand"
    )


class StaffWithdrawalFilters(BaseModel):
    status: WithdrawalStatus | None = Field(
        default=None, description="`pending` is the queue of requests to review"
    )
    seller_id: uuid.UUID | None = Field(default=None, description="One seller's withdrawals")
