from decimal import Decimal
from enum import StrEnum


class PlanStatus(StrEnum):
    ACTIVE = "active"
    RETIRED = "retired"  # no longer offered; existing subscriptions run their course


class SubscriptionStatus(StrEnum):
    PENDING = "pending"  # requested by the seller, waiting for an admin
    ACTIVE = "active"  # activated; applies between starts_at and ends_at
    REJECTED = "rejected"  # the request was declined
    CANCELLED = "cancelled"  # withdrawn, ended early, or replaced by another plan


class TermsSource(StrEnum):
    """Where a seller's commission rate comes from."""

    SUBSCRIPTION = "subscription"
    DEFAULT = "default"
    NOT_SET = "not_set"  # no subscription, and MUHUZE has not set a default rate yet


DEFAULT_CURRENCY = "RWF"

PLAN_CODE_PATTERN = r"^[a-z][a-z0-9_]{1,49}$"
PLAN_NAME_MAX_LENGTH = 100
PLAN_DESCRIPTION_MAX_LENGTH = 1000
# Ten years: a guard against typos, not a business limit.
PLAN_DURATION_DAYS_MAX = 3660

# NUMERIC(5, 2) percentages.
RATE_MAX = Decimal("100")
RATE_MAX_DIGITS = 5
RATE_DECIMAL_PLACES = 2
# NUMERIC(14, 2) money.
PRICE_MAX_DIGITS = 14
PRICE_DECIMAL_PLACES = 2

STATUS_REASON_MIN_LENGTH = 5
STATUS_REASON_MAX_LENGTH = 500
PAYMENT_REFERENCE_MAX_LENGTH = 100
NOTE_MAX_LENGTH = 500

REPLACED_REASON = "Replaced by a new plan"
