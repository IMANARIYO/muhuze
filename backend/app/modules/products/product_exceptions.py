from app.shared.exceptions.application_exceptions import (
    BusinessRuleError,
    ConflictError,
    InputValidationError,
    NotFoundError,
    ServiceUnavailableError,
)


class ProductNotFoundError(NotFoundError):
    message = "Product not found"


class ProductImageNotFoundError(NotFoundError):
    message = "Image not found"


class InvalidProductAttributesError(InputValidationError):
    message = "Invalid product attributes"


class ProductNotPublishableError(BusinessRuleError):
    message = "This product cannot be published yet"


class ProductStatusConflictError(ConflictError):
    message = "This action is not allowed in the product's current status"


class ProductHiddenByStaffError(ConflictError):
    message = "This product was hidden by MUHUZE and cannot be published"


class ProductNotDeletableError(ConflictError):
    message = "A product that has been published cannot be deleted. Archive it instead."


class TooManyProductImagesError(BusinessRuleError):
    message = "This product already has the maximum number of images"


class InvalidProductImageError(InputValidationError):
    message = "The image must be a JPEG or PNG"


class ProductImageTooLargeError(InputValidationError):
    message = "The image is too large"


class InvalidImageOrderError(InputValidationError):
    message = "Send every image of the product exactly once"


class ImageStorageUnavailableError(ServiceUnavailableError):
    message = "File storage is not available right now. Please try again later."
