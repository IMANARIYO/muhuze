from decimal import Decimal
from enum import StrEnum


class ProductStatus(StrEnum):
    DRAFT = "draft"  # being prepared; only its seller sees it
    PUBLISHED = "published"  # visible to buyers
    ARCHIVED = "archived"  # taken off sale by its seller; can be published again


class ProductKind(StrEnum):
    """What a listing offers. Chosen when it is created and never changed,
    because orders and requests depend on it (README §7.5)."""

    PRODUCT = "product"  # goods, bought through checkout
    SERVICE = "service"  # work done for the buyer, booked by request → accept → pay


class ServiceLocation(StrEnum):
    """Where a service is done (README §7.5, V15). Decides what a request
    asks of the buyer."""

    AT_CUSTOMER = "at_customer"  # the provider goes to the buyer: the buyer gives the address
    AT_PROVIDER = "at_provider"  # the buyer comes to the provider's shop
    ONLINE = "online"  # done remotely: no place at all


# A service's working hours are read in the marketplace's local time. One
# country for now, like the currency (README §20 T2, V18).
SERVICE_TIMEZONE = "Africa/Kigali"
SERVICE_DURATION_MAX_MINUTES = 7 * 24 * 60
SERVICE_MIN_NOTICE_MAX_HOURS = 30 * 24
SERVICE_AREAS_MAX = 50

# One currency for now (README §20 T2).
DEFAULT_CURRENCY = "RWF"

PRODUCT_NAME_MAX_LENGTH = 200
PRODUCT_SLUG_MAX_LENGTH = 220
PRODUCT_DESCRIPTION_MAX_LENGTH = 20_000
# NUMERIC(14, 2): up to 999,999,999,999.99.
PRICE_MAX_DIGITS = 14
PRICE_DECIMAL_PLACES = 2

ATTRIBUTE_TEXT_MAX_LENGTH = 500
# NUMERIC(18, 4)
ATTRIBUTE_NUMBER_LIMIT = Decimal("99999999999999.9999")
ATTRIBUTE_NUMBER_QUANTUM = Decimal("0.0001")

IMAGES_PER_PRODUCT_MAX = 8
IMAGE_MAX_BYTES = 5 * 1024 * 1024
# The type is decided from the file's first bytes, never from what the client claims.
IMAGE_SIGNATURES = (b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n")

SEARCH_QUERY_MAX_LENGTH = 100
