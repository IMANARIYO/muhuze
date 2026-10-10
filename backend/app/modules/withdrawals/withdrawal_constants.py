from decimal import Decimal
from enum import StrEnum

# Decided 2026-10-08 (README §13.8, §20 W4): the minimum is a fixed business
# rule; there is no maximum and no frequency limit (W5), and no fee (W3).
MINIMUM_AMOUNT = Decimal("1000")
DEFAULT_CURRENCY = "RWF"


class WithdrawalStatus(StrEnum):
    """README §13.8 lifecycle. `processing` means staff are paying it out."""

    PENDING = "pending"  # requested; funds reserved
    PROCESSING = "processing"  # approved; the payout is being made by hand
    COMPLETED = "completed"  # paid out
    REJECTED = "rejected"  # staff declined; funds returned
    FAILED = "failed"  # the payout did not go through; funds returned
    CANCELLED = "cancelled"  # the seller withdrew the request; funds returned


class PayoutDestinationType(StrEnum):
    """Decided 2026-10-08 (README §20 W8): mobile money or bank, data only."""

    MOBILE_MONEY = "mobile_money"
    BANK = "bank"


PROVIDER_MAX_LENGTH = 100
ACCOUNT_NUMBER_MAX_LENGTH = 100
ACCOUNT_NAME_MAX_LENGTH = 150
REASON_MIN_LENGTH = 5
REASON_MAX_LENGTH = 500
PAYOUT_REFERENCE_MAX_LENGTH = 100
