from app.shared.exceptions.base import ConflictError, NotFoundError, ValidationAppError


class SellerNotFoundError(NotFoundError):
    message = "Seller not found"


class SellerDocumentNotFoundError(NotFoundError):
    message = "Seller document not found"


class SellerAlreadyExistsError(ConflictError):
    message = "You already have a seller profile"


class BusinessNameAlreadyTakenError(ConflictError):
    message = "This business name is already taken"


class SellerNotEditableError(ConflictError):
    message = "This seller profile cannot be edited in its current status"


class SellerNotSubmittableError(ConflictError):
    message = "This seller profile cannot be submitted for review in its current status"


class SellerNotPendingReviewError(ConflictError):
    message = "This seller is not pending review"


class SellerNotActiveError(ConflictError):
    message = "This seller is not active"


class SellerNotSuspendedError(ConflictError):
    message = "This seller is not suspended"


class SellerNotDeactivatedError(ConflictError):
    message = "This seller is not deactivated"


class MissingRequiredDocumentsError(ValidationAppError):
    message = (
        "Required identity documents are missing — submit either both sides of a "
        "national ID, a passport, or a driving license"
    )
