import uuid
from datetime import timedelta

import jwt
import pytest

from app.core.clock import utc_now
from app.core.security import (
    InvalidAccessTokenError,
    build_password_hasher,
    create_access_token,
    decode_access_token,
    generate_opaque_token,
    generate_otp,
    hash_token,
)


async def test_password_is_hashed_and_verified(settings) -> None:
    hasher = build_password_hasher(settings)
    password_hash = await hasher.hash("correct-horse-battery")

    assert password_hash.startswith("$argon2")
    assert "correct-horse-battery" not in password_hash
    assert await hasher.verify("correct-horse-battery", password_hash)
    assert not await hasher.verify("wrong-password", password_hash)


async def test_same_password_hashes_differently_each_time(settings) -> None:
    hasher = build_password_hasher(settings)
    assert await hasher.hash("correct-horse-battery") != await hasher.hash("correct-horse-battery")


def test_otp_is_six_digits() -> None:
    for _ in range(50):
        code = generate_otp()
        assert len(code) == 6
        assert code.isdigit()


def test_opaque_tokens_are_unique_and_hash_deterministically() -> None:
    first, second = generate_opaque_token(), generate_opaque_token()
    assert first != second
    assert hash_token(first) == hash_token(first)
    assert hash_token(first) != hash_token(second)
    assert len(hash_token(first)) == 64


def test_access_token_round_trip(settings) -> None:
    account_id, session_id = uuid.uuid4(), uuid.uuid4()
    token = create_access_token(settings, account_id=account_id, session_id=session_id)

    claims = decode_access_token(settings, token)
    assert claims.account_id == account_id
    assert claims.session_id == session_id


def test_access_token_signed_with_another_secret_is_rejected(settings, make_settings) -> None:
    other = make_settings(jwt_secret_key="a-completely-different-secret-of-enough-length")
    token = create_access_token(other, account_id=uuid.uuid4(), session_id=uuid.uuid4())

    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(settings, token)


def _encode(settings, **claims: object) -> str:
    payload = {
        "sub": str(uuid.uuid4()),
        "sid": str(uuid.uuid4()),
        "type": "access",
        "exp": utc_now() + timedelta(minutes=5),
    }
    payload.update(claims)
    payload = {key: value for key, value in payload.items() if value is not None}
    return jwt.encode(
        payload, settings.jwt_secret_key.get_secret_value(), algorithm=settings.jwt_algorithm
    )


@pytest.mark.parametrize(
    "claims",
    [
        {"exp": utc_now() - timedelta(seconds=1)},  # expired
        {"type": "refresh"},  # not an access token
        {"sid": None},  # missing session id
        {"sub": "not-a-uuid"},
    ],
)
def test_invalid_access_tokens_are_rejected(settings, claims: dict[str, object]) -> None:
    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(settings, _encode(settings, **claims))


def test_garbage_access_token_is_rejected(settings) -> None:
    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(settings, "not.a.jwt")
