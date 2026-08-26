import re
import uuid

from httpx import AsyncClient


def unique_email() -> str:
    return f"test-{uuid.uuid4().hex}@example.com"


async def register_and_login(
    client: AsyncClient, password: str = "supersecret123"
) -> dict:
    email = unique_email()
    await client.post(
        "/api/v1/auth/register", json={"email": email, "password": password}
    )
    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    return response.json()["data"]


def auth_headers(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def extract_code(body: str) -> str:
    match = re.search(r"code is (\d{6})", body)
    assert match is not None, body
    return match.group(1)


async def test_request_email_verification_requires_auth(client: AsyncClient) -> None:
    response = await client.post("/api/v1/auth/email/verification/request")
    assert response.status_code == 401


async def test_request_email_verification_sends_a_code(
    client: AsyncClient, captured_emails: list[dict]
) -> None:
    tokens = await register_and_login(client)
    response = await client.post(
        "/api/v1/auth/email/verification/request", headers=auth_headers(tokens)
    )
    assert response.status_code == 200
    assert len(captured_emails) == 1
    extract_code(captured_emails[0]["body"])


async def test_confirm_with_correct_code_verifies_account(
    client: AsyncClient, captured_emails: list[dict]
) -> None:
    tokens = await register_and_login(client)
    headers = auth_headers(tokens)
    await client.post("/api/v1/auth/email/verification/request", headers=headers)
    code = extract_code(captured_emails[-1]["body"])

    response = await client.post(
        "/api/v1/auth/email/verification/confirm", json={"code": code}, headers=headers
    )
    assert response.status_code == 200


async def test_confirm_with_wrong_code_is_rejected(
    client: AsyncClient, captured_emails: list[dict]
) -> None:
    tokens = await register_and_login(client)
    headers = auth_headers(tokens)
    await client.post("/api/v1/auth/email/verification/request", headers=headers)

    response = await client.post(
        "/api/v1/auth/email/verification/confirm",
        json={"code": "000000"},
        headers=headers,
    )
    assert response.status_code == 401


async def test_confirming_the_same_code_twice_fails_the_second_time(
    client: AsyncClient, captured_emails: list[dict]
) -> None:
    tokens = await register_and_login(client)
    headers = auth_headers(tokens)
    await client.post("/api/v1/auth/email/verification/request", headers=headers)
    code = extract_code(captured_emails[-1]["body"])

    first = await client.post(
        "/api/v1/auth/email/verification/confirm", json={"code": code}, headers=headers
    )
    assert first.status_code == 200

    second = await client.post(
        "/api/v1/auth/email/verification/confirm", json={"code": code}, headers=headers
    )
    assert second.status_code == 401
