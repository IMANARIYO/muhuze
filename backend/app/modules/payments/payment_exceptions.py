from app.shared.exceptions.application_exceptions import (
    BusinessRuleError,
    ConflictError,
    NotFoundError,
)


class PaymentNotFoundError(NotFoundError):
    message = "Payment not found"


class PaymentDestinationNotFoundError(NotFoundError):
    message = "Payment destination not found"


class PaymentDestinationInUseError(ConflictError):
    message = "Payments have used this destination. Deactivate it instead of deleting it."


class InactiveDefaultDestinationError(BusinessRuleError):
    message = "Only an active destination can be the default"


class PaymentDestinationUnavailableError(BusinessRuleError):
    message = "This payment destination is not available. Choose one of the listed accounts."


class OrderNotPayableError(ConflictError):
    message = "This order is not waiting for payment"


class PaymentAlreadySubmittedError(ConflictError):
    message = "A payment for this order is already waiting to be verified"


class PaymentReferenceUsedError(ConflictError):
    message = "This transaction reference has already been used"


class PaymentStatusConflictError(ConflictError):
    message = "This action is not allowed in the payment's current status"


class OwnPaymentVerificationError(BusinessRuleError):
    message = "You cannot verify a payment you made yourself"


class PaymentAmountMismatchError(ConflictError):
    message = "The payment amount no longer matches the order total"
