import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints

from app.core.security import OTP_LENGTH
from app.modules.auth.auth_constants import (
    FULL_NAME_MAX_LENGTH,
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
    PHONE_PATTERN,
)

NewPassword = Annotated[
    str,
    Field(
        min_length=PASSWORD_MIN_LENGTH,
        max_length=PASSWORD_MAX_LENGTH,
        description=f"{PASSWORD_MIN_LENGTH} to {PASSWORD_MAX_LENGTH} characters",
    ),
]
# An existing password is only compared, so it has no minimum length.
ExistingPassword = Annotated[str, Field(min_length=1, max_length=PASSWORD_MAX_LENGTH)]
OpaqueToken = Annotated[str, Field(min_length=1, max_length=512)]


class RegisterRequest(BaseModel):
    email: EmailStr = Field(description="Login identifier; must be unique")
    password: NewPassword
    full_name: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=FULL_NAME_MAX_LENGTH),
    ]
    phone: str | None = Field(
        default=None,
        pattern=PHONE_PATTERN,
        description="Optional, E.164 format, e.g. +2507XXXXXXXX",
    )


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    phone: str | None
    full_name: str
    profile_picture: str | None
    status: str = Field(description="active | suspended | deactivated")
    is_verified: bool = Field(description="Whether the email address has been verified")
    created_at: datetime


class EmailVerificationRequest(BaseModel):
    email: EmailStr


class EmailVerificationConfirmRequest(BaseModel):
    email: EmailStr
    code: str = Field(
        pattern=rf"^\d{{{OTP_LENGTH}}}$", description=f"The {OTP_LENGTH}-digit code from the email"
    )


class LoginRequest(BaseModel):
    email: EmailStr
    password: ExistingPassword


class TokenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    access_token: str = Field(description="JWT; send as `Authorization: Bearer <token>`")
    refresh_token: str = Field(description="Opaque and single-use: each refresh returns a new one")
    token_type: Literal["bearer"] = "bearer"
    expires_in: int = Field(description="Access token lifetime in seconds")


class RefreshTokenRequest(BaseModel):
    refresh_token: OpaqueToken


class SessionResponse(BaseModel):
    id: uuid.UUID
    user_agent: str | None
    ip_address: str | None
    created_at: datetime = Field(description="When this session last logged in or refreshed")
    expires_at: datetime
    is_current: bool = Field(description="True for the session making this request")


class ChangePasswordRequest(BaseModel):
    current_password: ExistingPassword
    new_password: NewPassword


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: OpaqueToken
    new_password: NewPassword
