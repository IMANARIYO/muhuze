"""Persistence models for roles and permissions.

Mirrors `docs/database/database_schema.dbml`; change both together.
"""

import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint, false
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.modules.authorization.authorization_constants import (
    ROLE_DESCRIPTION_MAX_LENGTH,
    ROLE_NAME_MAX_LENGTH,
)


class Role(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Dynamic data: admins create, rename, and delete roles, except system roles."""

    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(ROLE_NAME_MAX_LENGTH), unique=True)
    description: Mapped[str | None] = mapped_column(String(ROLE_DESCRIPTION_MAX_LENGTH))
    is_system: Mapped[bool] = mapped_column(default=False, server_default=false())


class Permission(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A row of the code-defined catalog (app/core/permission_registry.py)."""

    __tablename__ = "permissions"
    __table_args__ = (UniqueConstraint("resource", "action"),)

    code: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(150))
    description: Mapped[str | None] = mapped_column(String(255))
    resource: Mapped[str] = mapped_column(String(50))
    action: Mapped[str] = mapped_column(String(50))


class AccountRole(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "account_roles"
    __table_args__ = (UniqueConstraint("account_id", "role_id"),)

    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"))
    role_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"), index=True
    )
    # Null = granted by the system (registration, bootstrap).
    granted_by_account_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("accounts.id", ondelete="SET NULL")
    )


class RolePermission(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "role_permissions"
    __table_args__ = (UniqueConstraint("role_id", "permission_id"),)

    role_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"))
    permission_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("permissions.id", ondelete="CASCADE"), index=True
    )


class AccountPermission(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """A permission granted straight to one account. Grant only: there is no "deny"."""

    __tablename__ = "account_permissions"
    __table_args__ = (UniqueConstraint("account_id", "permission_id"),)

    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"))
    permission_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("permissions.id", ondelete="CASCADE"), index=True
    )
    granted_by_account_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("accounts.id", ondelete="SET NULL")
    )
