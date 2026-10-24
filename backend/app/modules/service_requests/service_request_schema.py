import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import AwareDatetime, BaseModel, Field, StringConstraints

from app.modules.orders.order_constants import BUYER_NOTE_MAX_LENGTH
from app.modules.orders.order_schema import (
    DeliveryRequest,
    DeliveryResponse,
    OrderSummaryResponse,
)
from app.modules.service_requests.service_request_constants import ServiceRequestStatus

# ── Requests ─────────────────────────────────────────────────────────────
# Note what is NOT here: no price and no provider. The buyer names the
# service; the backend reads its price and shop (README §7.5).


class ServiceRequestCreateRequest(BaseModel):
    service_id: uuid.UUID = Field(description="A listing on offer whose `kind` is `service`")
    scheduled_for: AwareDatetime = Field(
        description="When you want it done, with a time zone. Must be in the future."
    )
    location: DeliveryRequest = Field(
        description="Where the service happens, and whom the provider contacts there"
    )
    note: (
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=BUYER_NOTE_MAX_LENGTH)]
        | None
    ) = Field(default=None, description="Anything the provider should know")


# ── Responses ────────────────────────────────────────────────────────────


class ServiceRequestResponse(BaseModel):
    """A service request, the same for the buyer, the provider, and staff:
    each sees only requests they are allowed to."""

    id: uuid.UUID
    status: ServiceRequestStatus
    status_reason: str | None = Field(description="Why it was declined or cancelled")
    service_id: uuid.UUID = Field(description="For a link to the listing; it may have changed")
    service_name: str = Field(description="As it was when requested")
    seller_id: uuid.UUID
    seller_name: str = Field(description="As it was when requested")
    buyer_account_id: uuid.UUID
    unit_price: Decimal = Field(description="What the buyer pays if it is accepted")
    currency: str
    scheduled_for: datetime
    location: DeliveryResponse
    responded_at: datetime | None
    cancelled_at: datetime | None
    created_at: datetime
    order: OrderSummaryResponse | None = Field(
        description="Set once accepted: the order the buyer pays, and its current status"
    )


# ── List filters ─────────────────────────────────────────────────────────


class ServiceRequestFilters(BaseModel):
    status: ServiceRequestStatus | None = Field(
        default=None, description="`requested` is what is waiting for an answer"
    )


class StaffServiceRequestFilters(ServiceRequestFilters):
    seller_id: uuid.UUID | None = Field(default=None, description="Only this provider")
    buyer_account_id: uuid.UUID | None = Field(default=None, description="Only this buyer")
