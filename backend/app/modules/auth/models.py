import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDPKMixin


class Account(UUIDPKMixin, TimestampMixin, Base):
    """The authenticatable identity. Personal info lives on users.Profile."""

    __tablename__ = "accounts"

    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    phone: Mapped[str | None] = mapped_column(
        String(20), unique=True, nullable=True, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class RefreshToken(UUIDPKMixin, TimestampMixin, Base):
    """Lets a client trade a still-valid refresh token for a new access token
    without re-authenticating. Only the hash is stored; the raw token is
    returned to the client once, at issuance."""

    __tablename__ = "refresh_tokens"

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class VerificationPurpose(StrEnum):
    EMAIL_VERIFICATION = "email_verification"
    PHONE_VERIFICATION = "phone_verification"


class VerificationCode(UUIDPKMixin, TimestampMixin, Base):
    """A one-time code proving control of an email/phone. Only the hash is
    stored. Multiple valid codes for the same account+purpose can coexist
    (e.g. a resend) — any one of them verifies successfully; using one
    doesn't invalidate the others, it just marks itself verified."""

    __tablename__ = "verification_codes"

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False, index=True
    )
    purpose: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    code_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class PasswordResetToken(UUIDPKMixin, TimestampMixin, Base):
    """Forgot-password flow. Deliberately not columns on Account — a user
    can request multiple resets; each token is single-use and expires."""

    __tablename__ = "password_reset_tokens"

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class Role(UUIDPKMixin, TimestampMixin, Base):
    """A named authorization grouping (buyer, seller, admin, ...). Seeded
    with defaults in the migration that creates this table."""

    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)


class Permission(UUIDPKMixin, TimestampMixin, Base):
    """A single capability, e.g. `products.delete`. The application code is
    the source of truth for which of these exist — see each module's own
    `permissions.py` and app/db/permissions.py — not this table directly.
    `python -m app.scripts.sync_permissions` reconciles code → database.
    Empty catalog is expected at first; populate as modules that need
    gating are built."""

    __tablename__ = "permissions"

    code: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resource: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)


class AccountRole(UUIDPKMixin, TimestampMixin, Base):
    """Many-to-many: which roles an account holds."""

    __tablename__ = "account_roles"
    __table_args__ = (
        UniqueConstraint("account_id", "role_id", name="uq_account_roles"),
    )

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False, index=True
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )


class RolePermission(UUIDPKMixin, TimestampMixin, Base):
    """Many-to-many: which permissions a role grants. Both FKs cascade on
    delete: deleting a Role drops its RolePermission rows (matching
    AccountRole.role_id's cascade — deleting a role should cleanly clear
    its grants, not be blocked by them), and the permission-sync script
    removing a stale permission cleans up its role assignments the same
    way."""

    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permissions"),
    )

    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )


class AccountPermission(UUIDPKMixin, TimestampMixin, Base):
    """A permission granted directly to an account, bypassing roles
    entirely. Independent of role membership in both directions: removing
    a role never removes a direct permission an account also holds, and
    revoking a direct permission never touches its roles. An account's
    effective permissions are the union of its roles' permissions and its
    direct permissions — see AuthorizationRepository.get_permission_codes.
    GRANT only, deliberately — no DENY/override semantics. Introducing a
    role-grants-but-account-denies precedence rule is a real design
    problem for a financial platform's authorization; the union-only
    model is simple and predictable, and precedence can be added later
    if a concrete need for it shows up."""

    __tablename__ = "account_permissions"
    __table_args__ = (
        UniqueConstraint("account_id", "permission_id", name="uq_account_permissions"),
    )

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False, index=True
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
