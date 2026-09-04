import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.orders.fulfillment_schemas import SellerOrderResponse


class ShippingInfoRequest(BaseModel):
    """An inline (free-form) delivery destination, used at checkout when the
    buyer isn't picking an already-saved address. Copied verbatim into the
    order's immutable `shipping_infos` snapshot."""

    recipient_name: str = Field(min_length=1, max_length=150, description="Who to hand it to")
    phone: str = Field(min_length=1, max_length=20, description="Delivery recipient phone")
    country: str = Field(default="Rwanda", max_length=60)
    province: str | None = Field(default=None, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    sector: str | None = Field(default=None, max_length=100)
    cell: str | None = Field(default=None, max_length=100)
    village: str | None = Field(default=None, max_length=100)
    address_line: str | None = Field(default=None, max_length=255)
    delivery_instructions: str | None = Field(default=None, max_length=255)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class CheckoutRequest(BaseModel):
    """Create an order from the buyer's cart. Either choose an already-saved
    `shipping_address_id`, or pass `shipping` inline (free-form). The chosen
    destination is snapshotted into the order's immutable `shipping_infos`
    row, so later edits to a saved address never change this order."""

    shipping_address_id: uuid.UUID | None = Field(
        default=None, description="A saved shipping_addresses.id to deliver to"
    )
    shipping: ShippingInfoRequest | None = Field(
        default=None, description="Free-form destination (used when no saved id given)"
    )
    contact_phone: str | None = Field(default=None, max_length=20)
    notes: str | None = Field(default=None, max_length=255)


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Order item ID")
    seller_id: uuid.UUID = Field(description="Which seller fulfills/earns this line")
    listing_id: uuid.UUID = Field(description="The seller offer bought")
    product_variant_id: uuid.UUID = Field(description="The variant bought")
    product_name: str = Field(description="Snapshot product name")
    variant_name: str | None = Field(description="Snapshot variant label")
    unit_price: float = Field(description="Snapshot unit price at purchase")
    quantity: int = Field(description="Quantity bought")
    subtotal: float = Field(description="unit_price * quantity")


class ShippingInfoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Snapshot ID")
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


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Order ID")
    order_number: str = Field(description="Human-readable order number")
    status: str = Field(description="Order lifecycle: pending | cancelled")
    payment_status: str = Field(description="pending | paid | failed | refunded | partially_refunded")
    subtotal: float = Field(description="Gross subtotal (sum of item subtotals)")
    shipping_fee: float = Field(description="Total delivery fee")
    discount_amount: float = Field(description="Promo discount (0 for now)")
    total_amount: float = Field(description="Total payable")
    currency: str = Field(description="Billing currency")
    paid_at: datetime | None = Field(description="When payment cleared (UTC)")
    completed_at: datetime | None = Field(description="When completed (UTC)")
    created_at: datetime = Field(description="When created (UTC)")
    updated_at: datetime = Field(description="When last updated (UTC)")
    items: list[OrderItemResponse] = Field(default_factory=list, description="The purchased lines")
    shipping: ShippingInfoResponse | None = Field(default=None, description="Immutable delivery snapshot")


class OrderDetailResponse(OrderResponse):
    """A buyer-facing order with its lines, delivery snapshot, and per-seller
    fulfillment status."""

    contact_phone: str | None = Field(default=None, description="Contact phone captured at checkout")
    notes: str | None = Field(default=None, description="Buyer notes")
    fulfillment: list[SellerOrderResponse] = Field(
        default_factory=list,
        description="Per-seller fulfillment state (pending -> accepted -> shipped -> delivered), "
        "each with its shipment",
    )


class OrderSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Order ID")
    order_number: str = Field(description="Human-readable order number")
    status: str = Field(description="Order lifecycle")
    payment_status: str = Field(description="Payment state")
    total_amount: float = Field(description="Total payable")
    currency: str = Field(description="Billing currency")
    created_at: datetime = Field(description="When created (UTC)")


class AdminOrderSummaryResponse(OrderSummaryResponse):
    """An order plus its single payment's own state, so an admin can see which
    orders are awaiting manual confirmation of the incoming MoMo."""

    payment_id: uuid.UUID | None = Field(
        default=None, description="The order's payment row, if one exists"
    )
    payment_status_detail: str | None = Field(
        default=None,
        description="The payment's own status (pending | awaiting | paid | failed), if a payment exists",
    )
