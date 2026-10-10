from app.shared.exceptions.application_exceptions import (
    BusinessRuleError,
    ConflictError,
    NotFoundError,
)


class CategoryNotFoundError(NotFoundError):
    message = "Category not found"


class CategoryAttributeNotFoundError(NotFoundError):
    message = "Attribute not found"


class CategoryAttributeOptionNotFoundError(NotFoundError):
    message = "Option not found"


class CategoryNameTakenError(ConflictError):
    message = "You already have a category with this name"


class CategoryAttributeNameTakenError(ConflictError):
    message = "This category already has an attribute with this name"


class CategoryAttributeOptionTakenError(ConflictError):
    message = "This attribute already has this option"


class CategoryInUseError(ConflictError):
    message = "This category still has products. Move them or switch the category off."


class CategoryAttributeInUseError(ConflictError):
    message = "Products already use this attribute. Switch it off instead."


class CategoryAttributeOptionInUseError(ConflictError):
    message = "Products already use this option. Switch it off instead."


class CategoryHiddenByStaffError(ConflictError):
    message = "This category was hidden by MUHUZE and cannot be reactivated"


class OptionsNotSupportedError(BusinessRuleError):
    message = "Only select and multi_select attributes have options"


class UnitNotSupportedError(BusinessRuleError):
    message = "Only number attributes have a unit"
