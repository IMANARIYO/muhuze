"""Authentication through the HTTP API, against a real PostgreSQL database.

Emails are captured by `email_outbox`; codes and reset links are read from it
the way a user would read them from their inbox.
"""

import re
from datetime import timedelta

import pytest
from httpx import AsyncClient, Response
from sqlalchemy import select, update

from app.core.clock import utc_now
from app.core.security import hash_token
from app.modules.auth.auth_model import (
    Account,
    PasswordResetToken,
    RefreshToken,
    VerificationCode,
)

AUTH = "/api/v1/auth"
EMAIL = "amina@example.com"
PASSWORD = "correct-horse-battery"
NEW_PASSWORD = "a-brand-new-password"


def registration(email: str = EMAIL, **overrides: object) -> dict[str, object]:
    return {"email": email, "password": PASSWORD, "full_name": "Amina Uwase", **overrides}


def bearer(tokens: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def emails_to(email_outbox, email: str) -> list[dict[str, str]]:
    return [message for message in email_outbox.sent if message["to"] == email]


def verification_code(email_outbox, email: str = EMAIL) -> str:
    body = emails_to(email_outbox, email)[-1]["body"]
    return re.search(r"\b(\d{6})\b", body).group(1)


def reset_token(email_outbox, email: str = EMAIL) -> str:
    body = emails_to(email_outbox, email)[-1]["body"]
    return re.search(r"token=([\w-]+)", body).group(1)


def a_wrong_code(right_code: str) -> str:
    return "000000" if right_code != "000000" else "111111"


async def register_and_verify(db_client: AsyncClient, email_outbox, email: str = EMAIL) -> None:
    response = await db_client.post(f"{AUTH}/register", json=registration(email))
    assert response.status_code == 201, response.text
    response = await db_client.post(
        f"{AUTH}/email/verification/confirm",
        json={"email": email, "code": verification_code(email_outbox, email)},
    )
    assert response.status_code == 200, response.text


async def login(
    db_client: AsyncClient,
    email: str = EMAIL,
    password: str = PASSWORD,
    user_agent: str = "pytest",
) -> Response:
    return await db_client.post(
        f"{AUTH}/login",
        json={"email": email, "password": password},
        headers={"User-Agent": user_agent},
    )


async def refresh(db_client: AsyncClient, refresh_token: str) -> Response:
    return await db_client.post(f"{AUTH}/refresh", json={"refresh_token": refresh_token})


@pytest.fixture
async def account(db_client: AsyncClient, email_outbox) -> str:
    """A registered and verified account; returns its email."""
    await register_and_verify(db_client, email_outbox)
    return EMAIL


@pytest.fixture
async def tokens(db_client: AsyncClient, account: str) -> dict:
    response = await login(db_client)
    assert response.status_code == 200, response.text
    return response.json()["data"]


@pytest.fixture
def db(session_factory):
    """Read or change rows directly, each call in its own short session."""

    class Database:
        async def one(self, statement):
            async with session_factory() as session:
                return (await session.execute(statement)).scalar_one()

        async def all(self, statement):
            async with session_factory() as session:
                return list((await session.execute(statement)).scalars())

        async def execute(self, statement) -> None:
            async with session_factory() as session:
                await session.execute(statement)
                await session.commit()

    return Database()


# ── Registration ─────────────────────────────────────────────────────────


async def test_register_creates_an_unverified_account_and_emails_a_code(
    db_client: AsyncClient, email_outbox, db
) -> None:
    response = await db_client.post(
        f"{AUTH}/register", json=registration("Amina@Example.COM", phone="+250788123456")
    )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["status_code"] == 201
    assert body["data"]["email"] == EMAIL  # stored lowercase
    assert body["data"]["full_name"] == "Amina Uwase"
    assert body["data"]["phone"] == "+250788123456"
    assert body["data"]["status"] == "active"
    assert body["data"]["is_verified"] is False
    assert "password" not in response.text

    stored = await db.one(select(Account).where(Account.email == EMAIL))
    assert stored.password_hash.startswith("$argon2")
    assert stored.is_verified is False

    (message,) = emails_to(email_outbox, EMAIL)
    code = verification_code(email_outbox)
    stored_code = await db.one(select(VerificationCode))
    assert stored_code.code_hash == hash_token(code)  # only the hash is stored
    assert code not in stored_code.code_hash
    assert message["subject"] == "Your MUHUZE verification code"


async def test_register_rejects_a_duplicate_email_in_any_letter_case(
    db_client: AsyncClient, account: str
) -> None:
    response = await db_client.post(f"{AUTH}/register", json=registration("AMINA@example.com"))

    assert response.status_code == 409
    assert response.json() == {
        "success": False,
        "data": None,
        "message": "An account with this email already exists",
        "status_code": 409,
    }


async def test_register_rejects_a_duplicate_phone(db_client: AsyncClient) -> None:
    phone = "+250788123456"
    first = await db_client.post(f"{AUTH}/register", json=registration(phone=phone))
    second = await db_client.post(
        f"{AUTH}/register", json=registration("other@example.com", phone=phone)
    )

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["message"] == "An account with this phone number already exists"


@pytest.mark.parametrize(
    "overrides",
    [
        {"password": "abc12"},
        {"password": "x" * 129},
        {"phone": "0788123456"},  # not E.164
        {"email": "not-an-email"},
        {"full_name": "   "},
    ],
)
async def test_register_validates_its_input(
    db_client: AsyncClient, overrides: dict[str, object]
) -> None:
    payload = registration(**overrides)
    response = await db_client.post(f"{AUTH}/register", json=payload)

    assert response.status_code == 422
    assert response.json()["success"] is False
    assert str(payload["password"]) not in response.text  # submitted values are never echoed


# ── Email verification ───────────────────────────────────────────────────


async def test_login_is_refused_until_the_email_is_verified(
    db_client: AsyncClient, email_outbox
) -> None:
    await db_client.post(f"{AUTH}/register", json=registration())

    refused = await login(db_client)
    assert refused.status_code == 403
    assert refused.json()["message"] == "Email address is not verified"

    confirmed = await db_client.post(
        f"{AUTH}/email/verification/confirm",
        json={"email": EMAIL, "code": verification_code(email_outbox)},
    )
    assert confirmed.status_code == 200

    assert (await login(db_client)).status_code == 200


async def test_unverified_account_with_wrong_password_gets_the_generic_error(
    db_client: AsyncClient,
) -> None:
    await db_client.post(f"{AUTH}/register", json=registration())

    response = await login(db_client, password="wrong-password")

    # Verification status is only revealed to someone who knows the password.
    assert response.status_code == 401
    assert response.json()["message"] == "Invalid email or password"


async def test_confirming_marks_the_account_verified_and_uses_up_the_code(
    db_client: AsyncClient, email_outbox, db
) -> None:
    await db_client.post(f"{AUTH}/register", json=registration())
    payload = {"email": EMAIL, "code": verification_code(email_outbox)}

    first = await db_client.post(f"{AUTH}/email/verification/confirm", json=payload)
    second = await db_client.post(f"{AUTH}/email/verification/confirm", json=payload)

    assert first.status_code == 200
    assert second.status_code == 400
    stored = await db.one(select(Account).where(Account.email == EMAIL))
    assert stored.is_verified is True
    assert stored.verified_at is not None
    assert (await db.one(select(VerificationCode))).used_at is not None


async def test_wrong_codes_are_counted_and_the_code_dies_after_the_limit(
    db_client: AsyncClient, email_outbox, db, settings
) -> None:
    await db_client.post(f"{AUTH}/register", json=registration())
    code = verification_code(email_outbox)
    url = f"{AUTH}/email/verification/confirm"

    for attempt in range(1, settings.verification_code_max_attempts + 1):
        response = await db_client.post(url, json={"email": EMAIL, "code": a_wrong_code(code)})
        assert response.status_code == 400
        assert response.json()["message"] == "Invalid or expired verification code"
        # The failed attempt is saved even though the request failed.
        assert (await db.one(select(VerificationCode))).attempts == attempt

    # The right code no longer works: the attempts are used up.
    response = await db_client.post(url, json={"email": EMAIL, "code": code})
    assert response.status_code == 400
    assert (await db.one(select(Account))).is_verified is False

    # A fresh code starts again from zero.
    await db_client.post(f"{AUTH}/email/verification/request", json={"email": EMAIL})
    response = await db_client.post(
        url, json={"email": EMAIL, "code": verification_code(email_outbox)}
    )
    assert response.status_code == 200


async def test_requesting_a_new_code_invalidates_the_previous_one(
    db_client: AsyncClient, email_outbox, db
) -> None:
    await db_client.post(f"{AUTH}/register", json=registration())
    old_code = verification_code(email_outbox)

    response = await db_client.post(f"{AUTH}/email/verification/request", json={"email": EMAIL})
    assert response.status_code == 200
    new_code = verification_code(email_outbox)
    assert len(emails_to(email_outbox, EMAIL)) == 2
    assert len(await db.all(select(VerificationCode))) == 1  # the old code is gone

    url = f"{AUTH}/email/verification/confirm"
    if old_code != new_code:
        old = await db_client.post(url, json={"email": EMAIL, "code": old_code})
        assert old.status_code == 400
    new = await db_client.post(url, json={"email": EMAIL, "code": new_code})
    assert new.status_code == 200


async def test_expired_code_is_rejected(db_client: AsyncClient, email_outbox, db) -> None:
    await db_client.post(f"{AUTH}/register", json=registration())
    await db.execute(update(VerificationCode).values(expires_at=utc_now() - timedelta(seconds=1)))

    response = await db_client.post(
        f"{AUTH}/email/verification/confirm",
        json={"email": EMAIL, "code": verification_code(email_outbox)},
    )

    assert response.status_code == 400


async def test_verification_request_does_not_reveal_which_emails_exist(
    db_client: AsyncClient, email_outbox, account: str
) -> None:
    sent_before = len(email_outbox.sent)

    unknown = await db_client.post(
        f"{AUTH}/email/verification/request", json={"email": "nobody@example.com"}
    )
    already_verified = await db_client.post(
        f"{AUTH}/email/verification/request", json={"email": account}
    )

    assert unknown.status_code == already_verified.status_code == 200
    assert unknown.json() == already_verified.json()
    assert len(email_outbox.sent) == sent_before  # nothing was sent for either

    confirm_unknown = await db_client.post(
        f"{AUTH}/email/verification/confirm", json={"email": "nobody@example.com", "code": "123456"}
    )
    assert confirm_unknown.status_code == 400
    assert confirm_unknown.json()["message"] == "Invalid or expired verification code"


# ── Login and access tokens ──────────────────────────────────────────────


async def test_login_returns_tokens_and_stores_only_the_refresh_token_hash(
    db_client: AsyncClient, account: str, db
) -> None:
    response = await login(db_client, email="AMINA@example.com", user_agent="Firefox on Linux")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 15 * 60

    stored = await db.one(select(RefreshToken))
    assert stored.token_hash == hash_token(data["refresh_token"])
    assert stored.revoked_at is None
    assert stored.user_agent == "Firefox on Linux"
    assert stored.ip_address is not None
    assert (await db.one(select(Account))).last_login_at is not None


async def test_login_gives_the_same_error_for_wrong_password_and_unknown_email(
    db_client: AsyncClient, account: str
) -> None:
    wrong_password = await login(db_client, password="wrong-password")
    unknown_email = await login(db_client, email="nobody@example.com")

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()
    assert wrong_password.json()["message"] == "Invalid email or password"


async def test_me_returns_the_callers_account(db_client: AsyncClient, tokens: dict) -> None:
    response = await db_client.get(f"{AUTH}/me", headers=bearer(tokens))

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["email"] == EMAIL
    assert data["is_verified"] is True
    assert "password_hash" not in data


async def test_protected_endpoints_reject_missing_or_invalid_access_tokens(
    db_client: AsyncClient, tokens: dict
) -> None:
    missing = await db_client.get(f"{AUTH}/me")
    garbage = await db_client.get(f"{AUTH}/me", headers={"Authorization": "Bearer not.a.jwt"})
    # A refresh token is not an access token.
    refresh_as_access = await db_client.get(
        f"{AUTH}/me", headers={"Authorization": f"Bearer {tokens['refresh_token']}"}
    )

    for response in (missing, garbage, refresh_as_access):
        assert response.status_code == 401
        assert response.json() == {
            "success": False,
            "data": None,
            "message": "Authentication required",
            "status_code": 401,
        }


async def test_suspended_account_is_locked_out_everywhere(
    db_client: AsyncClient, tokens: dict, db
) -> None:
    await db.execute(update(Account).values(status="suspended"))

    assert (await login(db_client)).status_code == 403
    assert (await db_client.get(f"{AUTH}/me", headers=bearer(tokens))).status_code == 401
    assert (await refresh(db_client, tokens["refresh_token"])).status_code == 401


# ── Refresh, logout, and sessions ────────────────────────────────────────


async def test_refresh_rotates_the_refresh_token(db_client: AsyncClient, tokens: dict, db) -> None:
    response = await refresh(db_client, tokens["refresh_token"])

    assert response.status_code == 200
    new_tokens = response.json()["data"]
    assert new_tokens["refresh_token"] != tokens["refresh_token"]
    assert (await db_client.get(f"{AUTH}/me", headers=bearer(new_tokens))).status_code == 200

    old = await db.one(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(tokens["refresh_token"]))
    )
    assert old.revoked_at is not None
    assert old.rotated_at is not None
    assert (await refresh(db_client, new_tokens["refresh_token"])).status_code == 200


async def test_reusing_a_rotated_refresh_token_ends_every_session(
    db_client: AsyncClient, tokens: dict, db
) -> None:
    other_device = (await login(db_client, user_agent="other device")).json()["data"]
    rotated = (await refresh(db_client, tokens["refresh_token"])).json()["data"]

    replay = await refresh(db_client, tokens["refresh_token"])

    assert replay.status_code == 401
    assert replay.json()["message"] == "Invalid or expired refresh token"
    # Neither the thief nor the owner keeps a session, on any device.
    assert (await refresh(db_client, rotated["refresh_token"])).status_code == 401
    assert (await refresh(db_client, other_device["refresh_token"])).status_code == 401
    assert all(token.revoked_at is not None for token in await db.all(select(RefreshToken)))


async def test_using_a_logged_out_token_does_not_end_other_sessions(
    db_client: AsyncClient, tokens: dict
) -> None:
    other_device = (await login(db_client, user_agent="other device")).json()["data"]
    await db_client.post(f"{AUTH}/logout", json={"refresh_token": other_device["refresh_token"]})

    # A logged-out token is simply invalid. Only a *rotated* token signals theft.
    assert (await refresh(db_client, other_device["refresh_token"])).status_code == 401
    assert (await refresh(db_client, tokens["refresh_token"])).status_code == 200


async def test_unknown_and_expired_refresh_tokens_are_rejected(
    db_client: AsyncClient, tokens: dict, db
) -> None:
    assert (await refresh(db_client, "never-issued")).status_code == 401

    await db.execute(update(RefreshToken).values(expires_at=utc_now() - timedelta(seconds=1)))
    assert (await refresh(db_client, tokens["refresh_token"])).status_code == 401


async def test_logout_ends_the_session_and_can_be_repeated(
    db_client: AsyncClient, tokens: dict
) -> None:
    payload = {"refresh_token": tokens["refresh_token"]}

    first = await db_client.post(f"{AUTH}/logout", json=payload)
    second = await db_client.post(f"{AUTH}/logout", json=payload)

    assert first.status_code == second.status_code == 200
    assert (await refresh(db_client, tokens["refresh_token"])).status_code == 401


async def test_logout_all_ends_every_session(db_client: AsyncClient, tokens: dict) -> None:
    other_device = (await login(db_client, user_agent="other device")).json()["data"]

    response = await db_client.post(f"{AUTH}/logout-all", headers=bearer(tokens))

    assert response.status_code == 200
    assert (await refresh(db_client, tokens["refresh_token"])).status_code == 401
    assert (await refresh(db_client, other_device["refresh_token"])).status_code == 401


async def test_sessions_are_listed_and_can_be_ended_one_by_one(
    db_client: AsyncClient, tokens: dict
) -> None:
    phone = (await login(db_client, user_agent="MUHUZE Android")).json()["data"]

    response = await db_client.get(f"{AUTH}/sessions", headers=bearer(tokens))

    assert response.status_code == 200
    page = response.json()["data"]
    assert page["total"] == 2
    assert page["page"] == 1
    current = [session for session in page["items"] if session["is_current"]]
    others = [session for session in page["items"] if not session["is_current"]]
    assert len(current) == len(others) == 1
    assert current[0]["user_agent"] == "pytest"
    assert others[0]["user_agent"] == "MUHUZE Android"
    assert "token_hash" not in others[0]

    ended = await db_client.delete(f"{AUTH}/sessions/{others[0]['id']}", headers=bearer(tokens))
    assert ended.status_code == 200
    assert (await refresh(db_client, phone["refresh_token"])).status_code == 401

    again = await db_client.delete(f"{AUTH}/sessions/{others[0]['id']}", headers=bearer(tokens))
    assert again.status_code == 404
    remaining = (await db_client.get(f"{AUTH}/sessions", headers=bearer(tokens))).json()["data"]
    assert remaining["total"] == 1


async def test_a_session_of_another_account_cannot_be_seen_or_ended(
    db_client: AsyncClient, email_outbox, tokens: dict
) -> None:
    other_email = "other@example.com"
    await register_and_verify(db_client, email_outbox, other_email)
    other_tokens = (await login(db_client, email=other_email)).json()["data"]
    other_sessions = await db_client.get(f"{AUTH}/sessions", headers=bearer(other_tokens))
    other_session_id = other_sessions.json()["data"]["items"][0]["id"]

    response = await db_client.delete(f"{AUTH}/sessions/{other_session_id}", headers=bearer(tokens))

    assert response.status_code == 404
    assert response.json()["message"] == "Session not found"
    assert (await refresh(db_client, other_tokens["refresh_token"])).status_code == 200
    mine = (await db_client.get(f"{AUTH}/sessions", headers=bearer(tokens))).json()["data"]
    assert mine["total"] == 1


# ── Passwords ────────────────────────────────────────────────────────────


async def test_change_password_needs_the_current_password(
    db_client: AsyncClient, tokens: dict
) -> None:
    response = await db_client.post(
        f"{AUTH}/password/change",
        json={"current_password": "wrong-password", "new_password": NEW_PASSWORD},
        headers=bearer(tokens),
    )

    assert response.status_code == 400
    assert response.json()["message"] == "Current password is incorrect"
    assert (await login(db_client)).status_code == 200  # unchanged


async def test_change_password_keeps_this_session_and_ends_the_others(
    db_client: AsyncClient, tokens: dict
) -> None:
    other_device = (await login(db_client, user_agent="other device")).json()["data"]

    response = await db_client.post(
        f"{AUTH}/password/change",
        json={"current_password": PASSWORD, "new_password": NEW_PASSWORD},
        headers=bearer(tokens),
    )

    assert response.status_code == 200
    assert (await login(db_client, password=PASSWORD)).status_code == 401
    assert (await login(db_client, password=NEW_PASSWORD)).status_code == 200
    assert (await refresh(db_client, other_device["refresh_token"])).status_code == 401
    assert (await refresh(db_client, tokens["refresh_token"])).status_code == 200


async def test_change_password_requires_authentication(db_client: AsyncClient) -> None:
    response = await db_client.post(
        f"{AUTH}/password/change",
        json={"current_password": PASSWORD, "new_password": NEW_PASSWORD},
    )
    assert response.status_code == 401


async def test_forgot_password_does_not_reveal_which_emails_exist(
    db_client: AsyncClient, email_outbox, account: str
) -> None:
    sent_before = len(email_outbox.sent)

    unknown = await db_client.post(f"{AUTH}/password/forgot", json={"email": "nobody@example.com"})
    known = await db_client.post(f"{AUTH}/password/forgot", json={"email": account})

    assert unknown.status_code == known.status_code == 200
    assert unknown.json() == known.json()
    assert len(email_outbox.sent) == sent_before + 1  # only the real account got an email
    assert email_outbox.sent[-1]["to"] == account


async def test_reset_password_sets_a_new_password_once_and_ends_every_session(
    db_client: AsyncClient, email_outbox, tokens: dict, db, settings
) -> None:
    await db_client.post(f"{AUTH}/password/forgot", json={"email": EMAIL})
    token = reset_token(email_outbox)
    assert f"{settings.password_reset_url}?token={token}" in email_outbox.sent[-1]["body"]
    stored = await db.one(select(PasswordResetToken))
    assert stored.token_hash == hash_token(token)  # only the hash is stored

    payload = {"token": token, "new_password": NEW_PASSWORD}
    first = await db_client.post(f"{AUTH}/password/reset", json=payload)
    second = await db_client.post(f"{AUTH}/password/reset", json=payload)

    assert first.status_code == 200
    assert second.status_code == 400  # single use
    assert second.json()["message"] == "Invalid or expired password reset token"
    assert (await login(db_client, password=PASSWORD)).status_code == 401
    assert (await login(db_client, password=NEW_PASSWORD)).status_code == 200
    assert (await refresh(db_client, tokens["refresh_token"])).status_code == 401


async def test_only_the_newest_reset_link_works(
    db_client: AsyncClient, email_outbox, account: str
) -> None:
    await db_client.post(f"{AUTH}/password/forgot", json={"email": account})
    old_token = reset_token(email_outbox)
    await db_client.post(f"{AUTH}/password/forgot", json={"email": account})
    new_token = reset_token(email_outbox)

    old = await db_client.post(
        f"{AUTH}/password/reset", json={"token": old_token, "new_password": NEW_PASSWORD}
    )
    new = await db_client.post(
        f"{AUTH}/password/reset", json={"token": new_token, "new_password": NEW_PASSWORD}
    )

    assert old.status_code == 400
    assert new.status_code == 200


async def test_unknown_and_expired_reset_tokens_are_rejected(
    db_client: AsyncClient, email_outbox, account: str, db
) -> None:
    unknown = await db_client.post(
        f"{AUTH}/password/reset", json={"token": "never-issued", "new_password": NEW_PASSWORD}
    )
    assert unknown.status_code == 400

    await db_client.post(f"{AUTH}/password/forgot", json={"email": account})
    await db.execute(update(PasswordResetToken).values(expires_at=utc_now() - timedelta(seconds=1)))
    expired = await db_client.post(
        f"{AUTH}/password/reset",
        json={"token": reset_token(email_outbox), "new_password": NEW_PASSWORD},
    )
    assert expired.status_code == 400
    assert (await login(db_client)).status_code == 200  # password unchanged
