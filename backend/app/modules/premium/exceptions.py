from app.shared.exceptions.base import ConflictError, NotFoundError


class PremiumPlanNotFoundError(NotFoundError):
    message = "Premium plan not found"


class PremiumPlanNotPurchasableError(ConflictError):
    message = "This premium plan is not currently available for purchase"


class SubscriptionNotFoundError(NotFoundError):
    message = "Subscription not found"


class NoActiveSubscriptionError(NotFoundError):
    message = "You do not have an active subscription"


class PlanCodeTakenError(ConflictError):
    message = "A premium plan with this code already exists"
