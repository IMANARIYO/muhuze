from enum import StrEnum


class PaymentMethod(StrEnum):
    MOBILE_MONEY = "mobile_money"
    MERCHANT_CODE = "merchant_code"
    BANK_TRANSFER = "bank_transfer"


class PaymentStatus(StrEnum):
    """Only the states a real flow needs today (README §12.2). `pending`,
    `refunded`, and others join when a gateway or refunds are built."""

    AWAITING_VERIFICATION = "awaiting_verification"  # the buyer submitted a reference
    PAID = "paid"  # staff (later: a gateway) confirmed the money arrived
    REJECTED = "rejected"  # the reference did not check out; the buyer may try again


class PaymentPurpose(StrEnum):
    ORDER = "order"


class PaymentChannel(StrEnum):
    """How a payment gets confirmed. One value per gateway joins in Phase 2."""

    MANUAL = "manual"


DEFAULT_CURRENCY = "RWF"

PROVIDER_MAX_LENGTH = 100
ACCOUNT_REFERENCE_MAX_LENGTH = 100
REGISTERED_NAME_MAX_LENGTH = 150
INSTRUCTIONS_MAX_LENGTH = 500
REFERENCE_MIN_LENGTH = 3
REFERENCE_MAX_LENGTH = 100
PAYER_NAME_MAX_LENGTH = 150
REASON_MIN_LENGTH = 5
REASON_MAX_LENGTH = 500
SEARCH_QUERY_MAX_LENGTH = 100
