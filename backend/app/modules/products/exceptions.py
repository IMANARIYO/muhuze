from app.shared.exceptions.base import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationAppError,
)


class BrandNotFoundError(NotFoundError):
    message = "Brand not found"


class BrandNameAlreadyTakenError(ConflictError):
    message = "A brand with this name already exists"


class AttributeNotFoundError(NotFoundError):
    message = "Attribute not found"


class ProductNotFoundError(NotFoundError):
    message = "Product not found"


class ProductCategoryNotFoundError(NotFoundError):
    message = "Category not found"


class ProductBrandNotFoundError(NotFoundError):
    message = "Brand not found"


class ProductVariantNotFoundError(NotFoundError):
    message = "Product variant not found"


class ProductImageNotFoundError(NotFoundError):
    message = "Product image not found"


class ProductNotEditableError(ConflictError):
    message = "This product cannot be edited in its current status"


class ProductNotSubmittableError(ConflictError):
    message = "This product cannot be submitted for review in its current status"


class ProductNotPendingReviewError(ConflictError):
    message = "This product is not pending review"


class ProductNotArchivableError(ConflictError):
    message = "Only an active product can be archived"


class ProductOwnershipError(ForbiddenError):
    message = "You do not own this product request"


class DuplicateVariantAttributesError(ValidationAppError):
    message = "Another variant of this product already has this exact combination of attribute values"


class DuplicateVariantAttributeError(ValidationAppError):
    message = "The same attribute was supplied more than once for this variant"


# --- seller listings -----------------------------------------------------------


class SellerNotFoundError(NotFoundError):
    message = "Seller profile not found"


class SellerNotActiveError(ConflictError):
    message = "You must be an active seller to manage listings"


class SellerListingNotFoundError(NotFoundError):
    message = "Listing not found"


class SellerListingImageNotFoundError(NotFoundError):
    message = "Listing image not found"


class DuplicateSellerListingError(ConflictError):
    message = "You already have a listing for this variant"


class ListingNotEditableError(ConflictError):
    message = "This listing cannot be edited in its current status"


class ListingNotSubmittableError(ConflictError):
    message = "This listing cannot be submitted for review in its current status"


class ListingNotApprovableError(ConflictError):
    message = "This listing is not pending review"


class ListingNotArchivableError(ConflictError):
    message = "Only an active listing can be archived"


class ListingNotUnarchivableError(ConflictError):
    message = "Only an archived listing can be unarchived"


class ListingNotSuspendableError(ConflictError):
    message = "Only an active listing can be suspended"


class ListingNotReactivatableError(ConflictError):
    message = "Only a suspended listing can be reactivated"


class ListingNotDeletableError(ConflictError):
    message = "Only a draft listing can be deleted"


class ListingPriceUpdateOnNonActiveError(ConflictError):
    message = "Price can only be updated on an active listing"


class ListingStockUpdateOnNonActiveError(ConflictError):
    message = "Stock can only be updated on an active listing"


class VariantNotActiveError(ConflictError):
    message = "The selected variant is not active"


class ProductNotActiveError(ConflictError):
    message = "The product for this variant is not active"


class SellerOwnershipError(ForbiddenError):
    message = "You do not own this listing"
