"""Security primitives: password hashing, opaque tokens, and JWT access tokens.

This module holds the mechanisms only. The rules for using them (who may log
in, when a token is revoked, …) live in `app/modules/auth/auth_service.py`.
PyJWT and pwdlib are not imported anywhere else.
"""

import asyncio
import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import timedelta

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from app.config.settings import Settings
from app.core.clock import utc_now

OTP_LENGTH = 6
ACCESS_TOKEN_TYPE = "access"  # noqa: S105 - a claim value, not a secret


class PasswordHasher:
    """Argon2 password hashing.

    Hashing is deliberately slow, so it runs in a worker thread and never
    blocks the event loop.
    """

    def __init__(self, password_hash: PasswordHash) -> None:
        self._password_hash = password_hash
        # Verified against when the account doesn't exist, so a login attempt
        # takes the same time whether or not the email is registered.
        self._dummy_hash = password_hash.hash(secrets.token_urlsafe(16))

    async def hash(self, password: str) -> str:
        return await asyncio.to_thread(self._password_hash.hash, password)

    async def verify(self, password: str, password_hash: str) -> bool:
        return await asyncio.to_thread(self._password_hash.verify, password, password_hash)

    async def verify_dummy(self, password: str) -> None:
        await self.verify(password, self._dummy_hash)


def build_password_hasher(settings: Settings) -> PasswordHasher:
    if settings.environment == "test":
        # Argon2's cost is the point in real environments; in tests it is
        # only overhead.
        return PasswordHasher(
            PasswordHash([Argon2Hasher(time_cost=1, memory_cost=8, parallelism=1)])
        )
    return PasswordHasher(PasswordHash.recommended())


def generate_opaque_token() -> str:
    """A high-entropy random token (refresh token, password reset token)."""
    return secrets.token_urlsafe(48)


def generate_otp() -> str:
    """A numeric one-time code, short enough to type from an email."""
    return f"{secrets.randbelow(10**OTP_LENGTH):0{OTP_LENGTH}d}"


def hash_token(token: str) -> str:
    """SHA-256 hex digest used to store and look up tokens and one-time codes.

    Not for passwords: those need `PasswordHasher`'s slow, salted hashing.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class AccessTokenClaims:
    account_id: uuid.UUID
    session_id: uuid.UUID


class InvalidAccessTokenError(Exception):
    """The access token is malformed, tampered with, expired, or not an access token."""


def create_access_token(settings: Settings, *, account_id: uuid.UUID, session_id: uuid.UUID) -> str:
    now = utc_now()
    payload = {
        "sub": str(account_id),
        "sid": str(session_id),
        "type": ACCESS_TOKEN_TYPE,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(
        payload, settings.jwt_secret_key.get_secret_value(), algorithm=settings.jwt_algorithm
    )


def decode_access_token(settings: Settings, token: str) -> AccessTokenClaims:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "sub", "sid", "type"]},
        )
        if payload["type"] != ACCESS_TOKEN_TYPE:
            raise InvalidAccessTokenError("not an access token")
        return AccessTokenClaims(
            account_id=uuid.UUID(payload["sub"]), session_id=uuid.UUID(payload["sid"])
        )
    except (jwt.InvalidTokenError, ValueError) as exc:
        raise InvalidAccessTokenError(str(exc)) from exc
