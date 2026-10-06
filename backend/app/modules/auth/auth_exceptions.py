from app.shared.exceptions.application_exceptions import (
    AuthenticationError,
    AuthorizationError,
    BadRequestError,
    ConflictError,
    NotFoundError,
)


class EmailAlreadyRegisteredError(ConflictError):
    message = "An account with this email already exists"


class PhoneAlreadyRegisteredError(ConflictError):
    message = "An account with this phone number already exists"


class InvalidCredentialsError(AuthenticationError):
    message = "Invalid email or password"


class InvalidRefreshTokenError(AuthenticationError):
    message = "Invalid or expired refresh token"


# The two errors below are raised only after the password was verified, so
# they reveal nothing to someone who doesn't already know it.
class EmailNotVerifiedError(AuthorizationError):
    message = "Email address is not verified"


class AccountNotActiveError(AuthorizationError):
    message = "This account is not active"


class InvalidVerificationCodeError(BadRequestError):
    message = "Invalid or expired verification code"


class InvalidPasswordResetTokenError(BadRequestError):
    message = "Invalid or expired password reset token"


# 400, not 401: the caller is authenticated, and a 401 would make clients
# treat the session as expired.
class IncorrectCurrentPasswordError(BadRequestError):
    message = "Current password is incorrect"


class SessionNotFoundError(NotFoundError):
    message = "Session not found"
