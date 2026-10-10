"""Application exceptions for expected failures.

Services raise these deliberately; the global handlers turn them into the
standard error envelope. Feature modules subclass the closest one (e.g.
`class ProductNotFoundError(NotFoundError)`) rather than inventing new
status-code mappings.

Anything that is NOT an AppError is treated as an unexpected failure: it is
logged with its stack trace and the client gets a generic 500.
"""


class AppError(Exception):
    status_code: int = 500
    message: str = "Internal server error"

    def __init__(self, message: str | None = None) -> None:
        if message is not None:
            self.message = message
        super().__init__(self.message)


class BadRequestError(AppError):
    status_code = 400
    message = "Bad request"


class AuthenticationError(AppError):
    status_code = 401
    message = "Authentication required"


class AuthorizationError(AppError):
    status_code = 403
    message = "You are not allowed to perform this action"


class NotFoundError(AppError):
    status_code = 404
    message = "Resource not found"


class ConflictError(AppError):
    status_code = 409
    message = "Resource conflict"


class InputValidationError(AppError):
    """Input is well-formed but invalid in a way only the service can tell.

    Named to avoid clashing with pydantic's ValidationError and FastAPI's
    RequestValidationError, which handle schema-level validation.
    """

    status_code = 422
    message = "Invalid input"


class BusinessRuleError(AppError):
    """The request is valid but a business rule forbids it (e.g. insufficient balance)."""

    status_code = 422
    message = "Business rule violated"


class ServiceUnavailableError(AppError):
    """Something the request depends on (file storage, …) is not available right now."""

    status_code = 503
    message = "Service temporarily unavailable"
