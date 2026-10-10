from app.shared.exceptions.application_exceptions import (
    BusinessRuleError,
    ConflictError,
    NotFoundError,
)


class WithdrawalNotFoundError(NotFoundError):
    message = "Withdrawal not found"


class NotASellerError(NotFoundError):
    message = "You do not have a seller account"


class PayoutDestinationNotFoundError(NotFoundError):
    message = "Payout destination not found"


class PayoutDestinationInUseError(ConflictError):
    message = "Withdrawals have used this destination. Deactivate it instead of deleting it."


class WithdrawalStatusConflictError(ConflictError):
    message = "This action is not allowed in the withdrawal's current status"


class AmountBelowMinimumError(BusinessRuleError):
    message = "The minimum withdrawal amount is 1,000 RWF"


class PayoutDestinationNotActiveError(BusinessRuleError):
    message = "This payout destination is deactivated. Choose an active one."
