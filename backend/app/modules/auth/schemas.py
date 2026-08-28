import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr = Field(description="Account email address (must be unique)")
    phone: str | None = Field(default=None, description="Optional phone number")
    password: str = Field(min_length=8, description="Password (minimum 8 characters)")


class LoginRequest(BaseModel):
    email: EmailStr = Field(description="Registered email address")
    password: str = Field(description="Account password")


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Account ID")
    email: str = Field(description="Account email address")
    phone: str | None = Field(description="Phone number (if provided)")
    is_active: bool = Field(description="Whether the account is active")
    is_verified: bool = Field(description="Whether the email has been verified")
    created_at: datetime = Field(description="When the account was created (UTC)")


class AccountWithRolesResponse(BaseModel):
    """Account plus the role names it holds — for admin directory views
    listing every account in one response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Account ID")
    email: str = Field(description="Account email address")
    phone: str | None = Field(description="Phone number (if provided)")
    is_active: bool = Field(description="Whether the account is active")
    is_verified: bool = Field(description="Whether the email has been verified")
    created_at: datetime = Field(description="When the account was created (UTC)")
    roles: list[str] = Field(description="Role names assigned to this account")


class TokenResponse(BaseModel):
    access_token: str = Field(description="JWT access token (short-lived)")
    refresh_token: str = Field(description="JWT refresh token (long-lived)")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(description="Valid refresh token to exchange for a new token pair")


class EmailVerificationConfirmRequest(BaseModel):
    code: str = Field(description="6-digit verification code sent to the email address")


class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(description="Registered email address to receive a reset code")


class ResetPasswordRequest(BaseModel):
    token: str = Field(description="Password reset token received via email")
    new_password: str = Field(min_length=8, description="New password (minimum 8 characters)")


class AuthorizationResponse(BaseModel):
    roles: list[str] = Field(description="List of role names assigned to this account")
    permissions: list[str] = Field(description="List of permission codes this account has")


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Role ID")
    name: str = Field(description="Role name (e.g. 'admin', 'seller', 'buyer')")
    description: str | None = Field(description="Human-readable role description")


class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Permission ID")
    code: str = Field(description="Permission code (e.g. 'products.create', 'listings.approve')")
    name: str = Field(description="Human-readable permission name")
    description: str | None = Field(description="Detailed permission description")
    resource: str = Field(description="Resource this permission applies to (e.g. 'products', 'listings', 'sellers')")
    action: str = Field(description="Action allowed (e.g. 'create', 'read', 'update', 'delete', 'approve')")


class AssignRoleRequest(BaseModel):
    role_name: str = Field(description="Role name to assign (must exist, e.g. 'admin', 'seller')")


class AssignPermissionRequest(BaseModel):
    permission_code: str = Field(description="Permission code to grant (must exist, e.g. 'products.create')")


class RoleCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=50, description="Role name (must be unique, e.g. 'moderator')")
    description: str | None = Field(default=None, description="Optional human-readable description")


class RoleUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=50, description="Role name (must be unique)")
    description: str | None = Field(default=None, description="Optional human-readable description")


class PermissionCreateRequest(BaseModel):
    code: str = Field(min_length=1, max_length=100, description="Permission code (must be unique, e.g. 'products.create')")
    name: str = Field(min_length=1, max_length=150, description="Human-readable permission name")
    description: str | None = Field(default=None, description="Detailed description of what this permission allows")
    resource: str = Field(min_length=1, max_length=50, description="Resource this permission applies to (e.g. 'products', 'listings')")
    action: str = Field(min_length=1, max_length=50, description="Action allowed (e.g. 'create', 'read', 'update', 'delete')")


class PermissionUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150, description="Human-readable permission name")
    description: str | None = Field(default=None, description="Detailed description")
    resource: str = Field(min_length=1, max_length=50, description="Resource this permission applies to")
    action: str = Field(min_length=1, max_length=50, description="Action allowed")
