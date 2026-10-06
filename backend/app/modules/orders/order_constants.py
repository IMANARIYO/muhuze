from enum import StrEnum


class OrderStatus(StrEnum):
    """The buyer's whole purchase. DERIVED by `derive_order_status`; never set directly."""

    AWAITING_PAYMENT = "awaiting_payment"
    IN_PROGRESS = "in_progress"  # paid; at least one shop is still working on its part
    COMPLETED = "completed"  # every part is finished and at least one was received
    CANCELLED = "cancelled"  # cancelled before payment, or every part was rejected


class SellerOrderStatus(StrEnum):
    """One shop's part of an order."""

    AWAITING_PAYMENT = "awaiting_payment"  # not yet shown to the seller
    PENDING = "pending"  # paid; waiting for the seller to accept or reject
    ACCEPTED = "accepted"
    SHIPPED = "shipped"
    DELIVERED = "delivered"  # the seller says it arrived
    COMPLETED = "completed"  # the buyer confirmed receipt
    REJECTED = "rejected"  # the seller declined it
    CANCELLED = "cancelled"  # the order was cancelled before payment


# A seller order in one of these will not change again.
FINAL_SELLER_ORDER_STATUSES = frozenset(
    {SellerOrderStatus.COMPLETED, SellerOrderStatus.REJECTED, SellerOrderStatus.CANCELLED}
)

DEFAULT_CURRENCY = "RWF"
ORDER_NUMBER_PREFIX = "MHZ-"
ORDER_NUMBER_SEQUENCE = "order_number_seq"

ITEMS_PER_ORDER_MAX = 50
ITEM_QUANTITY_MAX = 999

RECIPIENT_NAME_MAX_LENGTH = 150
ADDRESS_PART_MAX_LENGTH = 100
DELIVERY_ADDRESS_MAX_LENGTH = 255
BUYER_NOTE_MAX_LENGTH = 500
REASON_MIN_LENGTH = 5
REASON_MAX_LENGTH = 500
IMAGE_URL_MAX_LENGTH = 500
SEARCH_QUERY_MAX_LENGTH = 20
