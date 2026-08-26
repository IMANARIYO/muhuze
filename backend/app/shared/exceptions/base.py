class AppError(Exception):
    """Base class for domain/application errors that map to a standard HTTP response."""

    status_code: int = 500
    message: str = "Internal server error"

    def __init__(self, message: str | None = None) -> None:
        if message is not None:
            self.message = message
        super().__init__(self.message)


class BadRequestError(AppError):
    status_code = 400
    message = "Bad request"


class UnauthorizedError(AppError):
    status_code = 401
    message = "Unauthorized"


class ForbiddenError(AppError):
    status_code = 403
    message = "Forbidden"


class NotFoundError(AppError):
    status_code = 404
    message = "Resource not found"


class ConflictError(AppError):
    status_code = 409
    message = "Resource conflict"


class ValidationAppError(AppError):
    status_code = 422
    message = "Validation error"


class ServiceUnavailableError(AppError):
    status_code = 503
    message = "Service unavailable"
