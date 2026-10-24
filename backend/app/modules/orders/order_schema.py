import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.modules.auth.auth_constants import PHONE_PATTERN
from app.modules.orders.order_constants import (
    ADDRESS_PART_MAX_LENGTH,
    BUYER_NOTE_MAX_LENGTH,
    DELIVERY_ADDRESS_MAX_LENGTH,
    ITEM_QUANTITY_MAX,
    ITEMS_PER_ORDER_MAX,
    REASON_MAX_LENGTH,
    REASON_MIN_LENGTH,
    RECIPIENT_NAME_MAX_LENGTH,
    SEARCH_QUERY_MAX_LENGTH,
    OrderKind,
    OrderStatus,
    SellerOrderStatus,
)
from app.modules.products.product_constants import ServiceLocation

AddressPart = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=ADDRESS_PART_MAX_LENGTH),
]
Reason = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True, min_length=REASON_MIN_LENGTH, max_length=REASON_MAX_LENGTH
    ),
]

# ── Placing an order ─────────────────────────────────────────────────────
# Note what is NOT here: no price, no total, no seller. The client says what
# and how many; the backend decides everything else (README §8).


class OrderItemRequest(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(ge=1, le=ITEM_QUANTITY_MAX)


RecipientName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=RECIPIENT_NAME_MAX_LENGTH),
]
Phone = Annotated[str, Field(pattern=PHONE_PATTERN, description="E.164, e.g. +2507XXXXXXXX")]


class DeliveryPlace(BaseModel):
    """A place in Rwanda: where goods are delivered, or where a service done
    at the buyer's place happens."""

    province: AddressPart
    district: AddressPart
    sector: AddressPart
    address: (
        Annotated[
            str, StringConstraints(strip_whitespace=True, max_length=DELIVERY_ADDRESS_MAX_LENGTH)
        ]
        | None
    ) = Field(default=None, description="Street, building, landmark")


class DeliveryRequest(DeliveryPlace):
    recipient_name: RecipientName
    recipient_phone: Phone


class OrderCreateRequest(BaseModel):
    items: list[OrderItemRequest] = Field(min_length=1, max_length=ITEMS_PER_ORDER_MAX)
    delivery: DeliveryRequest
    note: (
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=BUYER_NOTE_MAX_LENGTH)]
        | None
    ) = Field(default=None, description="Anything the sellers should know")

    @model_validator(mode="after")
    def _each_product_once(self) -> Self:
        product_ids = [item.product_id for item in self.items]
        if len(product_ids) != len(set(product_ids)):
            raise ValueError("a product can appear only once; use quantity")
        return self


class OrderCancelRequest(BaseModel):
    reason: Reason | None = None


class ReasonRequest(BaseModel):
    reason: Reason = Field(description="Shown to the buyer")


# ── Responses ────────────────────────────────────────────────────────────


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID = Field(description="For a link to the product; it may have changed")
    product_name: str = Field(description="As it was when ordered")
    unit_price: Decimal = Field(description="As it was when ordered")
    quantity: int
    line_total: Decimal
    image_url: str | None
    attributes: list[dict[str, Any]] = Field(
        description='The product\'s details when ordered: [{"name", "value", "unit"}]'
    )


class DeliveryResponse(BaseModel):
    """Where to deliver and whom to contact. For a service order: whom to
    contact, and where the service happens. The place is null for a service
    done at the provider's place or online (README §7.5, V15)."""

    recipient_name: str
    recipient_phone: str
    province: str | None
    district: str | None
    sector: str | None
    address: str | None
    note: str | None


class ProviderAddressResponse(BaseModel):
    """Where to go for a service done at the provider's place."""

    province: str
    district: str
    sector: str
    street_address: str | None


class SellerOrderEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    from_status: SellerOrderStatus | None
    to_status: SellerOrderStatus
    reason: str | None
    actor_account_id: uuid.UUID | None
    created_at: datetime


class BuyerSellerOrderResponse(BaseModel):
    """One shop's part of the order, as the BUYER sees it: no commission."""

    id: uuid.UUID
    seller_id: uuid.UUID
    seller_name: str
    status: SellerOrderStatus
    status_reason: str | None
    subtotal: Decimal
    provider_phone: str | None = Field(
        default=None,
        description=(
            "A service order only, once it is paid: the provider's business phone, "
            "with or without a subscription. Null otherwise (README §7.5, V14)"
        ),
    )
    provider_address: ProviderAddressResponse | None = Field(
        default=None,
        description=(
            "A paid `at_provider` service order only: the shop's address, where to go. "
            "Null otherwise (README §7.5, V15)"
        ),
    )
    items: list[OrderItemResponse]


class OrderSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_number: str
    kind: OrderKind = Field(description="`product` (a checkout) or `service` (an accepted request)")
    scheduled_for: datetime | None = Field(description="A service order: the agreed time")
    service_location: ServiceLocation | None = Field(
        description="A service order: `at_customer`, `at_provider`, or `online`"
    )
    status: OrderStatus
    currency: str
    total_amount: Decimal
    paid_at: datetime | None
    cancelled_at: datetime | None
    created_at: datetime


class OrderResponse(OrderSummaryResponse):
    """The buyer's whole order."""

    cancel_reason: str | None
    delivery: DeliveryResponse
    seller_orders: list[BuyerSellerOrderResponse]


class SellerOrderSummaryResponse(BaseModel):
    """One row of a seller's order list."""

    id: uuid.UUID
    order_number: str
    kind: OrderKind
    scheduled_for: datetime | None = Field(description="A service order: the agreed time")
    service_location: ServiceLocation | None = Field(
        description="A service order: `at_customer`, `at_provider`, or `online`"
    )
    status: SellerOrderStatus
    currency: str
    subtotal: Decimal
    seller_amount: Decimal = Field(description="What the seller earns from it")
    recipient_name: str
    paid_at: datetime | None
    created_at: datetime


class SellerOrderResponse(SellerOrderSummaryResponse):
    """One shop's part of an order, as the SELLER sees it: their own items
    and money split, and where to deliver. Never other shops' parts."""

    seller_id: uuid.UUID
    order_id: uuid.UUID
    status_reason: str | None
    commission_rate: Decimal
    commission_amount: Decimal = Field(description="MUHUZE's share")
    plan_name: str | None = Field(description="The plan that gave the rate; null = default rate")
    delivery: DeliveryResponse
    items: list[OrderItemResponse]
    events: list[SellerOrderEventResponse]


class StaffSellerOrderResponse(BuyerSellerOrderResponse):
    commission_rate: Decimal
    commission_amount: Decimal
    seller_amount: Decimal
    terms_source: str
    plan_name: str | None
    events: list[SellerOrderEventResponse]


class StaffOrderResponse(OrderSummaryResponse):
    buyer_account_id: uuid.UUID
    cancel_reason: str | None
    delivery: DeliveryResponse
    seller_orders: list[StaffSellerOrderResponse]


# ── List filters ─────────────────────────────────────────────────────────


class OwnOrderFilters(BaseModel):
    status: OrderStatus | None = None


class SellerOrderFilters(BaseModel):
    status: SellerOrderStatus | None = Field(
        default=None, description="`pending` is what is waiting for you to accept or reject"
    )


class StaffOrderFilters(BaseModel):
    status: OrderStatus | None = None
    buyer_account_id: uuid.UUID | None = None
    q: str | None = Field(
        default=None,
        min_length=1,
        max_length=SEARCH_QUERY_MAX_LENGTH,
        description="Search by order number (contains, case-insensitive)",
    )
