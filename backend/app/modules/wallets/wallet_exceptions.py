from app.shared.exceptions.application_exceptions import ConflictError, NotFoundError


class WalletNotFoundError(NotFoundError):
    message = "This seller has no wallet"


class NotASellerError(NotFoundError):
    message = "You do not have a seller wallet"


class EarningNotRecordedError(ConflictError):
    """A seller order is being settled or reversed, but no earning was ever
    recorded for it. Never expected: it means the order was not paid through
    the payment confirmation."""

    message = "No earning was recorded for this order"


class EarningAlreadySettledError(ConflictError):
    message = "This earning has already been released to the seller and cannot be reversed here"


class EarningReversedError(ConflictError):
    message = "This earning was reversed and cannot be released"
