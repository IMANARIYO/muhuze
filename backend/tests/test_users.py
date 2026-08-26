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


async def test_get_profile_without_token_is_rejected(client: AsyncClient) -> None:
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401


async def test_get_profile_with_garbage_token_is_rejected(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/users/me", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert response.status_code == 401


async def test_get_profile_before_creation_is_404(client: AsyncClient) -> None:
    tokens = await register_and_login(client)
    response = await client.get("/api/v1/users/me", headers=auth_headers(tokens))
    assert response.status_code == 404


async def test_create_and_fetch_profile(client: AsyncClient) -> None:
    tokens = await register_and_login(client)
    headers = auth_headers(tokens)

    create_response = await client.put(
        "/api/v1/users/me",
        json={
            "first_name": "Ada",
            "last_name": "Lovelace",
            "date_of_birth": "1990-01-01",
        },
        headers=headers,
    )
    assert create_response.status_code == 200
    body = create_response.json()["data"]
    assert body["first_name"] == "Ada"
    assert body["last_name"] == "Lovelace"
    assert body["date_of_birth"] == "1990-01-01"

    get_response = await client.get("/api/v1/users/me", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["data"]["first_name"] == "Ada"


async def test_upsert_profile_updates_existing(client: AsyncClient) -> None:
    tokens = await register_and_login(client)
    headers = auth_headers(tokens)

    await client.put(
        "/api/v1/users/me",
        json={"first_name": "Ada", "last_name": "Lovelace"},
        headers=headers,
    )
    update_response = await client.put(
        "/api/v1/users/me",
        json={"first_name": "Grace", "last_name": "Hopper"},
        headers=headers,
    )
    assert update_response.status_code == 200
    body = update_response.json()["data"]
    assert body["first_name"] == "Grace"
    assert body["last_name"] == "Hopper"

    get_response = await client.get("/api/v1/users/me", headers=headers)
    assert get_response.json()["data"]["first_name"] == "Grace"


async def test_profile_is_scoped_to_the_authenticated_account(
    client: AsyncClient,
) -> None:
    tokens_a = await register_and_login(client)
    tokens_b = await register_and_login(client)

    await client.put(
        "/api/v1/users/me",
        json={"first_name": "Ada", "last_name": "Lovelace"},
        headers=auth_headers(tokens_a),
    )

    response_b = await client.get("/api/v1/users/me", headers=auth_headers(tokens_b))
    assert response_b.status_code == 404
