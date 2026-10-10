import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, StringConstraints

from app.modules.authorization.authorization_constants import (
    ROLE_DESCRIPTION_MAX_LENGTH,
    ROLE_NAME_PATTERN,
)


def _normalize_role_name(value: object) -> object:
    return value.strip().lower() if isinstance(value, str) else value


RoleName = Annotated[
    str,
    # Runs first: "  Support_Agent " is accepted and stored as "support_agent".
    BeforeValidator(_normalize_role_name),
    StringConstraints(pattern=ROLE_NAME_PATTERN),
    Field(description="2 to 50 lowercase letters, digits, or underscores; starts with a letter"),
]
RoleDescription = Annotated[
    str, StringConstraints(strip_whitespace=True, max_length=ROLE_DESCRIPTION_MAX_LENGTH)
]


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    is_system: bool = Field(description="System roles cannot be renamed or deleted")
    created_at: datetime


class RoleCreateRequest(BaseModel):
    name: RoleName
    description: RoleDescription | None = None


class RoleUpdateRequest(BaseModel):
    """Only the fields that are sent are changed."""

    name: RoleName | None = None
    description: RoleDescription | None = None


class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str = Field(description="<resource>.<action>, e.g. product.create")
    name: str
    description: str | None
    resource: str
    action: str


class PermissionFilters(BaseModel):
    resource: str | None = Field(
        default=None, max_length=50, description="Only permissions of this resource, e.g. role"
    )


class AccountAuthorizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    roles: list[str] = Field(description="Names of the roles the account holds")
    permissions: list[str] = Field(
        description="Every permission code the account has, through its roles or directly"
    )
