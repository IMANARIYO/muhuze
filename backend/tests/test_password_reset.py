import re
import uuid

from httpx import AsyncClient


def unique_email() -> str:
    return f"test-{uuid.uuid4().hex}@example.com"


def extract_token(body: str) -> str:
    match = re.search(r"token is (\S+)\.", body)
    assert match is not None, body
    return match.group(1)


async def test_forgot_password_always_returns_success_for_unknown_email(
    client: AsyncClient, captured_emails: list[dict]
) -> None:
    response = await client.post(
        "/api/v1/auth/password/forgot", json={"email": unique_email()}
    )
    assert response.status_code == 200
    assert captured_emails == []


async def test_forgot_password_sends_a_token_for_a_known_account(
    client: AsyncClient, captured_emails: list[dict]
) -> None:
    email = unique_email()
    await client.post(
        "/api/v1/auth/register", json={"email": email, "password": "supersecret123"}
    )

    response = await client.post("/api/v1/auth/password/forgot", json={"email": email})
    assert response.status_code == 200
    assert len(captured_emails) == 1
    assert captured_emails[0]["to"] == email
    extract_token(captured_emails[0]["body"])


async def test_reset_password_with_valid_token_allows_login_with_new_password(
    client: AsyncClient, captured_emails: list[dict]
) -> None:
    email = unique_email()
    await client.post(
        "/api/v1/auth/register", json={"email": email, "password": "old-password123"}
    )
    await client.post("/api/v1/auth/password/forgot", json={"email": email})
    token = extract_token(captured_emails[-1]["body"])

    reset_response = await client.post(
        "/api/v1/auth/password/reset",
        json={"token": token, "new_password": "new-password456"},
    )
    assert reset_response.status_code == 200

    old_login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "old-password123"}
    )
    assert old_login.status_code == 401

    new_login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "new-password456"}
    )
    assert new_login.status_code == 200


async def test_reset_password_revokes_existing_refresh_tokens(
    client: AsyncClient, captured_emails: list[dict]
) -> None:
    email = unique_email()
    await client.post(
        "/api/v1/auth/register", json={"email": email, "password": "old-password123"}
    )
    login_response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "old-password123"}
    )
    old_refresh_token = login_response.json()["data"]["refresh_token"]

    await client.post("/api/v1/auth/password/forgot", json={"email": email})
    token = extract_token(captured_emails[-1]["body"])
    await client.post(
        "/api/v1/auth/password/reset",
        json={"token": token, "new_password": "new-password456"},
    )

    refresh_response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": old_refresh_token}
    )
    assert refresh_response.status_code == 401


async def test_reset_password_with_invalid_token_is_rejected(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/auth/password/reset",
        json={"token": "not-a-real-token", "new_password": "new-password456"},
    )
    assert response.status_code == 401


async def test_reset_password_token_is_single_use(
    client: AsyncClient, captured_emails: list[dict]
) -> None:
    email = unique_email()
    await client.post(
        "/api/v1/auth/register", json={"email": email, "password": "old-password123"}
    )
    await client.post("/api/v1/auth/password/forgot", json={"email": email})
    token = extract_token(captured_emails[-1]["body"])

    first = await client.post(
        "/api/v1/auth/password/reset",
        json={"token": token, "new_password": "new-password456"},
    )
    assert first.status_code == 200

    second = await client.post(
        "/api/v1/auth/password/reset",
        json={"token": token, "new_password": "another-password789"},
    )
    assert second.status_code == 401
