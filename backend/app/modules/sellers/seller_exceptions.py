from app.shared.exceptions.application_exceptions import (
    AuthorizationError,
    BusinessRuleError,
    ConflictError,
    InputValidationError,
    NotFoundError,
    ServiceUnavailableError,
)


class SellerNotFoundError(NotFoundError):
    message = "Seller not found"


class SellerApplicationNotFoundError(NotFoundError):
    message = "You have not applied to become a seller"


class SellerDocumentNotFoundError(NotFoundError):
    message = "Document not found"


class SellerAlreadyExistsError(ConflictError):
    message = "You already have a seller application"


class BusinessNameTakenError(ConflictError):
    message = "This business name is already taken"


class SellerNotEditableError(ConflictError):
    message = "The application can only be changed while it is a draft or after a rejection"


class SellerStatusConflictError(ConflictError):
    """The requested status change isn't allowed from the seller's current status."""

    message = "This action is not allowed in the seller's current status"


class MissingSellerDocumentsError(BusinessRuleError):
    message = "Required documents are missing"


class OwnApplicationReviewError(BusinessRuleError):
    message = "You cannot review your own seller application"


class SellerNotActiveError(AuthorizationError):
    message = "Only an approved, active seller can do this"


class InvalidDocumentFileError(InputValidationError):
    message = "The file must be a JPEG, PNG, or PDF"


class DocumentTooLargeError(InputValidationError):
    message = "The file is too large"


class FileStorageUnavailableError(ServiceUnavailableError):
    message = "File storage is not available right now. Please try again later."
