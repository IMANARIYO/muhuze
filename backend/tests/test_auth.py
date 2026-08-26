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


async def test_register_creates_account(client: AsyncClient) -> None:
    email = unique_email()
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "supersecret123"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["email"] == email
    assert body["data"]["is_active"] is True
    assert "password" not in body["data"]


async def test_register_duplicate_email_is_rejected(client: AsyncClient) -> None:
    email = unique_email()
    payload = {"email": email, "password": "supersecret123"}
    await client.post("/api/v1/auth/register", json=payload)
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    assert response.json()["status"] == "error"


async def test_login_with_correct_credentials_returns_tokens(
    client: AsyncClient,
) -> None:
    email = unique_email()
    password = "supersecret123"
    await client.post(
        "/api/v1/auth/register", json={"email": email, "password": password}
    )

    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["token_type"] == "bearer"
    assert body["data"]["access_token"]
    assert body["data"]["refresh_token"]


async def test_login_with_wrong_password_is_rejected(client: AsyncClient) -> None:
    email = unique_email()
    await client.post(
        "/api/v1/auth/register", json={"email": email, "password": "supersecret123"}
    )

    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "wrong-password"}
    )
    assert response.status_code == 401
    assert response.json()["status"] == "error"


async def test_login_with_unknown_email_is_rejected(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/login", json={"email": unique_email(), "password": "whatever123"}
    )
    assert response.status_code == 401


async def test_refresh_returns_new_tokens(client: AsyncClient) -> None:
    tokens = await register_and_login(client)

    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["refresh_token"] != tokens["refresh_token"]


async def test_refresh_rotates_old_token_so_it_cannot_be_reused(
    client: AsyncClient,
) -> None:
    tokens = await register_and_login(client)

    first = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert first.status_code == 200

    reuse = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert reuse.status_code == 401


async def test_refresh_with_garbage_token_is_rejected(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": "not-a-real-token"}
    )
    assert response.status_code == 401


async def test_logout_revokes_refresh_token(client: AsyncClient) -> None:
    tokens = await register_and_login(client)

    logout_response = await client.post(
        "/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]}
    )
    assert logout_response.status_code == 200

    refresh_response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert refresh_response.status_code == 401


async def test_logout_with_unknown_token_is_idempotent(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/logout", json={"refresh_token": "not-a-real-token"}
    )
    assert response.status_code == 200
