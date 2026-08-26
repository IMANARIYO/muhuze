import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    phone: str | None = None
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AccountResponse(BaseModel):
    id: uuid.UUID
    email: str
    phone: str | None
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class EmailVerificationConfirmRequest(BaseModel):
    code: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class AuthorizationResponse(BaseModel):
    roles: list[str]
    permissions: list[str]


class RoleResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None

    model_config = {"from_attributes": True}


class PermissionResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    description: str | None
    resource: str
    action: str

    model_config = {"from_attributes": True}


class AssignRoleRequest(BaseModel):
    role_name: str


class AssignPermissionRequest(BaseModel):
    permission_code: str
