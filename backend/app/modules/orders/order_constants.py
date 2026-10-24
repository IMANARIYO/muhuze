from enum import StrEnum


class OrderKind(StrEnum):
    """How the order came about. Decides the path its seller order takes
    after payment (README §7.5, §9.3)."""

    PRODUCT = "product"  # a checkout of goods from the cart
    SERVICE = "service"  # one service request the provider accepted


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
    ACCEPTED = "accepted"  # a service order starts here once paid
    SHIPPED = "shipped"  # goods only
    DELIVERED = "delivered"  # the seller says it arrived; for a service: says it was done
    COMPLETED = "completed"  # the buyer confirmed receipt, or that the service was done
    REJECTED = "rejected"  # the seller declined it, or the provider cannot do a paid service
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
