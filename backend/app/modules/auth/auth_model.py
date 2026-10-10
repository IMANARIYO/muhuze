"""Persistence models for authentication.

Mirrors `docs/database/database_schema.dbml`; change both together.
"""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, SmallInteger, String, false
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.modules.auth.auth_constants import (
    FULL_NAME_MAX_LENGTH,
    USER_AGENT_MAX_LENGTH,
    AccountStatus,
    VerificationPurpose,
)


def _in_values(column: str, enum: type[AccountStatus] | type[VerificationPurpose]) -> str:
    return f"{column} IN ({', '.join(repr(member.value) for member in enum)})"


class Account(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One row per person, whatever they do on MUHUZE (README §3, §6.2)."""

    __tablename__ = "accounts"
    __table_args__ = (
        CheckConstraint("email = lower(email)", name="email_lowercase"),
        CheckConstraint(_in_values("status", AccountStatus), name="status_valid"),
    )

    email: Mapped[str] = mapped_column(String(255), unique=True)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(FULL_NAME_MAX_LENGTH))
    profile_picture: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(
        String(20), default=AccountStatus.ACTIVE.value, server_default=AccountStatus.ACTIVE.value
    )
    status_reason: Mapped[str | None] = mapped_column(String(255))
    status_changed_at: Mapped[datetime | None]
    is_verified: Mapped[bool] = mapped_column(default=False, server_default=false())
    verified_at: Mapped[datetime | None]
    last_login_at: Mapped[datetime | None]


class RefreshToken(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """One row per session. Rotation revokes the row and inserts a new one.

    `revoked_at` ends the session for any reason. `rotated_at` is also set
    when the reason was a refresh, which is what makes a later reuse of that
    token recognisable as theft (as opposed to a token that was logged out).
    """

    __tablename__ = "refresh_tokens"

    account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime]
    revoked_at: Mapped[datetime | None]
    rotated_at: Mapped[datetime | None]
    user_agent: Mapped[str | None] = mapped_column(String(USER_AGENT_MAX_LENGTH))
    ip_address: Mapped[str | None] = mapped_column(String(45))


class VerificationCode(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "verification_codes"
    __table_args__ = (
        CheckConstraint(_in_values("purpose", VerificationPurpose), name="purpose_valid"),
        CheckConstraint("attempts >= 0", name="attempts_not_negative"),
        Index("ix_verification_codes_account_id_purpose", "account_id", "purpose"),
    )

    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"))
    purpose: Mapped[str] = mapped_column(String(30))
    code_hash: Mapped[str] = mapped_column(String(64))
    attempts: Mapped[int] = mapped_column(SmallInteger, default=0, server_default="0")
    expires_at: Mapped[datetime]
    used_at: Mapped[datetime | None]


class PasswordResetToken(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "password_reset_tokens"

    account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime]
    used_at: Mapped[datetime | None]
