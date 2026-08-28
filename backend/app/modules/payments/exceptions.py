from app.shared.exceptions.base import BadRequestError, NotFoundError


class PaymentNotFoundError(NotFoundError):
    message = "Payment not found"


class PaymentAlreadyProcessedError(BadRequestError):
    message = "This payment has already been processed"
