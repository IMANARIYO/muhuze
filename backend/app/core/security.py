import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from app.core.config import settings

# Argon2's cost is the whole point in dev/production — it's deliberately
# slow to resist brute-forcing. In tests that same slowness (~160ms per
# hash) is pure overhead with no security benefit, and dominates the test
# suite's runtime far more than the database does. ENVIRONMENT=test is set
# by tests/conftest.py, before this module is first imported.
password_hasher = (
    PasswordHash([Argon2Hasher(time_cost=1, memory_cost=8, parallelism=1)])
    if settings.environment == "test"
    else PasswordHash.recommended()
)


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hasher.verify(password, hashed_password)


def generate_refresh_token() -> str:
    """A high-entropy opaque token, not a JWT. Returned to the client once."""
    return secrets.token_urlsafe(64)


def generate_password_reset_token() -> str:
    """A high-entropy opaque token, not a JWT. Returned to the client once."""
    return secrets.token_urlsafe(64)


def generate_otp() -> str:
    """A 6-digit numeric code, suitable for a human to type in from an email."""
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_token(token: str) -> str:
    """Deterministic digest for storing/looking up opaque tokens (refresh tokens,
    OTPs, password-reset tokens). Not for passwords — those need `hash_password`'s
    slow, salted hashing; tokens are already high-entropy, so a fast, unsalted
    digest that supports exact-match lookup by hash is the correct tool here.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(
    subject: str, extra_claims: dict[str, Any] | None = None
) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload: dict[str, Any] = {"sub": subject, "exp": expire}
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
    )
