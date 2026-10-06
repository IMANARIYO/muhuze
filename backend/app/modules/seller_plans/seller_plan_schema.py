import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Self

from pydantic import (
    AwareDatetime,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)

from app.modules.seller_plans.seller_plan_constants import (
    NOTE_MAX_LENGTH,
    PAYMENT_REFERENCE_MAX_LENGTH,
    PLAN_CODE_PATTERN,
    PLAN_DESCRIPTION_MAX_LENGTH,
    PLAN_DURATION_DAYS_MAX,
    PLAN_NAME_MAX_LENGTH,
    PRICE_DECIMAL_PLACES,
    PRICE_MAX_DIGITS,
    RATE_DECIMAL_PLACES,
    RATE_MAX,
    RATE_MAX_DIGITS,
    STATUS_REASON_MAX_LENGTH,
    STATUS_REASON_MIN_LENGTH,
    PlanStatus,
    SubscriptionStatus,
    TermsSource,
)


def _normalize_code(value: object) -> object:
    return value.strip().lower() if isinstance(value, str) else value


PlanCode = Annotated[
    str,
    BeforeValidator(_normalize_code),
    StringConstraints(pattern=PLAN_CODE_PATTERN),
    Field(description="Stable key: 2 to 50 lowercase letters, digits, or underscores"),
]
PlanName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=PLAN_NAME_MAX_LENGTH)
]
PlanDescription = Annotated[
    str, StringConstraints(strip_whitespace=True, max_length=PLAN_DESCRIPTION_MAX_LENGTH)
]
# Decimals, never floats. Serialized as strings ("10000.00", "7.50").
Price = Annotated[
    Decimal,
    Field(
        ge=0,
        max_digits=PRICE_MAX_DIGITS,
        decimal_places=PRICE_DECIMAL_PLACES,
        description="Subscription fee for one period; 0 for a free plan",
    ),
]
Rate = Annotated[
    Decimal,
    Field(
        ge=0,
        le=RATE_MAX,
        max_digits=RATE_MAX_DIGITS,
        decimal_places=RATE_DECIMAL_PLACES,
        description="Percent of each sale MUHUZE keeps: 0 to 100",
    ),
]
DurationDays = Annotated[
    int, Field(gt=0, le=PLAN_DURATION_DAYS_MAX, description="Length of one period, in days")
]
Reason = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=STATUS_REASON_MIN_LENGTH,
        max_length=STATUS_REASON_MAX_LENGTH,
    ),
    Field(description="Shown to the seller"),
]
PaymentReference = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=PAYMENT_REFERENCE_MAX_LENGTH),
    Field(description="What was checked before activating: a MoMo or bank reference"),
]


# ── Plans ────────────────────────────────────────────────────────────────


class SellerPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    description: str | None
    price: Decimal
    currency: str
    duration_days: int
    commission_rate: Decimal
    status: PlanStatus
    created_at: datetime


class SellerPlanCreateRequest(BaseModel):
    code: PlanCode
    name: PlanName
    description: PlanDescription | None = None
    price: Price
    duration_days: DurationDays
    commission_rate: Rate


class SellerPlanUpdateRequest(BaseModel):
    """Only the fields that are sent are changed. The code cannot be changed.
    Existing subscriptions keep the terms they started with."""

    name: PlanName | None = None
    description: PlanDescription | None = None
    price: Price | None = None
    duration_days: DurationDays | None = None
    commission_rate: Rate | None = None

    @model_validator(mode="after")
    def _required_fields_cannot_be_cleared(self) -> Self:
        for field in self.model_fields_set - {"description"}:
            if getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


class StaffPlanFilters(BaseModel):
    status: PlanStatus | None = None


# ── Subscriptions ────────────────────────────────────────────────────────


class SellerSubscriptionResponse(BaseModel):
    id: uuid.UUID
    seller_id: uuid.UUID
    plan_id: uuid.UUID
    plan_name: str
    price: Decimal = Field(description="The fee for this period, as agreed when it was requested")
    currency: str
    duration_days: int
    commission_rate: Decimal = Field(description="The rate while this subscription applies")
    status: SubscriptionStatus
    starts_at: datetime | None
    ends_at: datetime | None
    is_applicable: bool = Field(description="True if this is the subscription in force right now")
    status_reason: str | None
    payment_reference: str | None
    decided_at: datetime | None
    created_at: datetime


class SubscriptionRequest(BaseModel):
    plan_id: uuid.UUID


class SubscriptionAssignRequest(BaseModel):
    seller_id: uuid.UUID
    plan_id: uuid.UUID
    payment_reference: PaymentReference | None = None


class SubscriptionActivateRequest(BaseModel):
    payment_reference: PaymentReference | None = None


class ReasonRequest(BaseModel):
    reason: Reason


class StaffSubscriptionFilters(BaseModel):
    seller_id: uuid.UUID | None = None
    plan_id: uuid.UUID | None = None
    status: SubscriptionStatus | None = Field(
        default=None, description="`pending` is the queue of requests waiting for a decision"
    )


class CommercialTermsResponse(BaseModel):
    """What a seller is charged on each sale right now, and why."""

    commission_rate: Decimal | None = Field(
        description="Percent of each sale MUHUZE keeps; null if no rate has been set yet"
    )
    source: TermsSource
    subscription: SellerSubscriptionResponse | None = Field(
        description="The subscription in force, when the rate comes from one"
    )
    upcoming: list[SellerSubscriptionResponse] = Field(
        description="Activated subscriptions that have not started yet"
    )
    pending_request: SellerSubscriptionResponse | None = Field(
        description="A plan request waiting for a decision"
    )


# ── Default commission rate ──────────────────────────────────────────────


class DefaultCommissionRateResponse(BaseModel):
    id: uuid.UUID
    rate: Decimal
    effective_from: datetime
    note: str | None
    set_by_account_id: uuid.UUID | None
    created_at: datetime
    is_current: bool = Field(description="True for the rate in force right now")


class DefaultCommissionRateRequest(BaseModel):
    rate: Rate
    effective_from: AwareDatetime | None = Field(
        default=None, description="When it starts to apply, with a time zone. Omit for now"
    )
    note: (
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=NOTE_MAX_LENGTH)] | None
    ) = None
