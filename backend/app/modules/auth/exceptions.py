from app.shared.exceptions.base import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)


class EmailAlreadyRegisteredError(ConflictError):
    message = "An account with this email already exists"


class InvalidCredentialsError(UnauthorizedError):
    message = "Invalid email or password"


class InvalidRefreshTokenError(UnauthorizedError):
    message = "Invalid or expired refresh token"


class UnauthenticatedError(UnauthorizedError):
    message = "Authentication required"


class InvalidVerificationCodeError(UnauthorizedError):
    message = "Invalid or expired verification code"


class InvalidPasswordResetTokenError(UnauthorizedError):
    message = "Invalid or expired password reset token"


class InsufficientPermissionsError(ForbiddenError):
    message = "You do not have permission to perform this action"


class AccountNotFoundError(NotFoundError):
    message = "Account not found"


class RoleNotFoundError(NotFoundError):
    message = "Role not found"


class PermissionNotFoundError(NotFoundError):
    message = "Permission not found"
