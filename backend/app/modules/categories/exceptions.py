from app.shared.exceptions.base import ConflictError, NotFoundError, ValidationAppError


class CategoryNotFoundError(NotFoundError):
    message = "Category not found"


class CategoryParentNotFoundError(NotFoundError):
    message = "Parent category not found"


class DuplicateCategoryNameError(ConflictError):
    message = "A category with this name already exists under the same parent"


class SelfParentError(ValidationAppError):
    message = "A category cannot be its own parent"


class CircularParentError(ConflictError):
    message = "Moving this category would create a circular relationship"


class CategoryMoveError(ConflictError):
    message = "Category cannot be moved in its current status"
