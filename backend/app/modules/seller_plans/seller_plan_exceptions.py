from app.shared.exceptions.application_exceptions import (
    BusinessRuleError,
    ConflictError,
    InputValidationError,
    NotFoundError,
)


class SellerPlanNotFoundError(NotFoundError):
    message = "Plan not found"


class SellerSubscriptionNotFoundError(NotFoundError):
    message = "Subscription not found"


class SellerPlanCodeTakenError(ConflictError):
    message = "A plan with this code already exists"


class SellerPlanInUseError(ConflictError):
    message = "Sellers have subscribed to this plan. Retire it instead of deleting it."


class SellerPlanRetiredError(BusinessRuleError):
    message = "This plan is no longer offered"


class PendingSubscriptionExistsError(ConflictError):
    message = "You already have a plan request waiting for a decision"


class SubscriptionStatusConflictError(ConflictError):
    message = "This action is not allowed in the subscription's current status"


class SubscriptionPeriodConflictError(ConflictError):
    message = "This seller already has a subscription for that period. Please try again."


class DefaultCommissionRateNotSetError(BusinessRuleError):
    message = "MUHUZE has not set its commission rate yet"


class EffectiveDateInPastError(InputValidationError):
    message = "The rate can only take effect now or in the future"


class EffectiveDateTakenError(ConflictError):
    message = "A rate is already set to take effect at that exact moment"
