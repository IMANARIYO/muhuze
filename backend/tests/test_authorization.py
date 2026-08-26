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


async def test_authorization_endpoint_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me/authorization")
    assert response.status_code == 401


async def test_new_account_gets_buyer_role_by_default(client: AsyncClient) -> None:
    tokens = await register_and_login(client)
    response = await client.get(
        "/api/v1/auth/me/authorization", headers=auth_headers(tokens)
    )
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["roles"] == ["buyer"]
    assert body["permissions"] == []


async def test_my_roles_endpoint_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me/roles")
    assert response.status_code == 401


async def test_my_roles_endpoint_returns_just_roles(client: AsyncClient) -> None:
    tokens = await register_and_login(client)
    response = await client.get("/api/v1/auth/me/roles", headers=auth_headers(tokens))
    assert response.status_code == 200
    assert response.json()["data"] == ["buyer"]


async def test_my_permissions_endpoint_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me/permissions")
    assert response.status_code == 401


async def test_my_permissions_endpoint_returns_just_permissions(
    client: AsyncClient,
) -> None:
    tokens = await register_and_login(client)
    response = await client.get(
        "/api/v1/auth/me/permissions", headers=auth_headers(tokens)
    )
    assert response.status_code == 200
    assert response.json()["data"] == []
