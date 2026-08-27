import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.repository import AccountRepository, AuthorizationRepository


def unique_email() -> str:
    return f"category-test-{uuid.uuid4().hex}@example.com"


def unique_name() -> str:
    return f"Category {uuid.uuid4().hex}"


async def register_and_login(
    client: AsyncClient, password: str = "supersecret123"
) -> tuple[str, dict]:
    email = unique_email()
    await client.post(
        "/api/v1/auth/register", json={"email": email, "password": password}
    )
    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    return email, response.json()["data"]


async def make_admin(client: AsyncClient, db: AsyncSession) -> dict:
    email, tokens = await register_and_login(client)
    account = await AccountRepository(db).get_by_email(email)
    assert account is not None
    admin_role = await AuthorizationRepository(db).get_role_by_name("admin")
    assert admin_role is not None
    await AuthorizationRepository(db).assign_role(
        account_id=account.id, role_id=admin_role.id
    )
    await db.commit()
    return tokens


def auth_headers(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


# --- create -----------------------------------------------------------------


async def test_create_requires_admin(client: AsyncClient) -> None:
    _, tokens = await register_and_login(client)
    response = await client.post(
        "/api/v1/categories",
        json={"name": unique_name()},
        headers=auth_headers(tokens),
    )
    assert response.status_code == 403


async def test_create_requires_auth(client: AsyncClient) -> None:
    response = await client.post("/api/v1/categories", json={"name": unique_name()})
    assert response.status_code == 401


async def test_admin_creates_top_level_category(
    client: AsyncClient, db: AsyncSession
) -> None:
    tokens = await make_admin(client, db)
    name = unique_name()
    response = await client.post(
        "/api/v1/categories", json={"name": name}, headers=auth_headers(tokens)
    )
    assert response.status_code == 201
    body = response.json()["data"]
    assert body["name"] == name
    assert body["parent_id"] is None
    assert body["status"] == "active"
    assert body["slug"]


async def test_slug_collision_gets_numeric_suffix(
    client: AsyncClient, db: AsyncSession
) -> None:
    tokens = await make_admin(client, db)
    headers = auth_headers(tokens)

    first = await client.post(
        "/api/v1/categories", json={"name": "Cafe Menu"}, headers=headers
    )
    second = await client.post(
        "/api/v1/categories", json={"name": "cafe menu"}, headers=headers
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["data"]["slug"] != second.json()["data"]["slug"]
    assert second.json()["data"]["slug"].startswith(first.json()["data"]["slug"])


async def test_duplicate_name_same_parent_is_409(
    client: AsyncClient, db: AsyncSession
) -> None:
    tokens = await make_admin(client, db)
    headers = auth_headers(tokens)
    name = "Duplicate Name"

    first = await client.post(
        "/api/v1/categories", json={"name": name}, headers=headers
    )
    second = await client.post(
        "/api/v1/categories", json={"name": name}, headers=headers
    )
    assert first.status_code == 201
    assert second.status_code == 409


async def test_create_child_category(client: AsyncClient, db: AsyncSession) -> None:
    tokens = await make_admin(client, db)
    headers = auth_headers(tokens)
    parent = await client.post(
        "/api/v1/categories", json={"name": unique_name()}, headers=headers
    )
    parent_id = parent.json()["data"]["id"]

    child = await client.post(
        "/api/v1/categories",
        json={"name": unique_name(), "parent_id": parent_id},
        headers=headers,
    )
    assert child.status_code == 201
    assert child.json()["data"]["parent_id"] == parent_id


async def test_create_with_unknown_parent_is_404(
    client: AsyncClient, db: AsyncSession
) -> None:
    tokens = await make_admin(client, db)
    response = await client.post(
        "/api/v1/categories",
        json={"name": unique_name(), "parent_id": str(uuid.uuid4())},
        headers=auth_headers(tokens),
    )
    assert response.status_code == 404


# --- read ---------------------------------------------------------------


async def test_get_unknown_category_is_404(client: AsyncClient) -> None:
    response = await client.get(f"/api/v1/categories/{uuid.uuid4()}")
    assert response.status_code == 404


async def test_get_and_list_do_not_require_auth(
    client: AsyncClient, db: AsyncSession
) -> None:
    tokens = await make_admin(client, db)
    created = await client.post(
        "/api/v1/categories", json={"name": unique_name()}, headers=auth_headers(tokens)
    )
    category_id = created.json()["data"]["id"]

    get_response = await client.get(f"/api/v1/categories/{category_id}")
    assert get_response.status_code == 200

    list_response = await client.get("/api/v1/categories")
    assert list_response.status_code == 200
    assert any(c["id"] == category_id for c in list_response.json()["data"])


async def test_list_top_level_excludes_children(
    client: AsyncClient, db: AsyncSession
) -> None:
    tokens = await make_admin(client, db)
    headers = auth_headers(tokens)
    parent = await client.post(
        "/api/v1/categories", json={"name": unique_name()}, headers=headers
    )
    parent_id = parent.json()["data"]["id"]
    child = await client.post(
        "/api/v1/categories",
        json={"name": unique_name(), "parent_id": parent_id},
        headers=headers,
    )
    child_id = child.json()["data"]["id"]

    roots = await client.get("/api/v1/categories/roots")
    root_ids = [c["id"] for c in roots.json()["data"]]
    assert parent_id in root_ids
    assert child_id not in root_ids


async def test_list_children(client: AsyncClient, db: AsyncSession) -> None:
    tokens = await make_admin(client, db)
    headers = auth_headers(tokens)
    parent = await client.post(
        "/api/v1/categories", json={"name": unique_name()}, headers=headers
    )
    parent_id = parent.json()["data"]["id"]
    child = await client.post(
        "/api/v1/categories",
        json={"name": unique_name(), "parent_id": parent_id},
        headers=headers,
    )
    child_id = child.json()["data"]["id"]

    response = await client.get(f"/api/v1/categories/{parent_id}/children")
    assert response.status_code == 200
    assert [c["id"] for c in response.json()["data"]] == [child_id]


async def test_list_children_of_unknown_category_is_404(client: AsyncClient) -> None:
    response = await client.get(f"/api/v1/categories/{uuid.uuid4()}/children")
    assert response.status_code == 404


# --- update ------------------------------------------------------------------


async def test_admin_updates_category(client: AsyncClient, db: AsyncSession) -> None:
    tokens = await make_admin(client, db)
    headers = auth_headers(tokens)
    created = await client.post(
        "/api/v1/categories", json={"name": unique_name()}, headers=headers
    )
    category_id = created.json()["data"]["id"]

    response = await client.patch(
        f"/api/v1/categories/{category_id}",
        json={"name": "Renamed", "status": "inactive"},
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["name"] == "Renamed"
    assert body["status"] == "inactive"


async def test_update_requires_admin(client: AsyncClient, db: AsyncSession) -> None:
    tokens = await make_admin(client, db)
    created = await client.post(
        "/api/v1/categories", json={"name": unique_name()}, headers=auth_headers(tokens)
    )
    category_id = created.json()["data"]["id"]

    _, other_tokens = await register_and_login(client)
    response = await client.patch(
        f"/api/v1/categories/{category_id}",
        json={"name": "Renamed", "status": "active"},
        headers=auth_headers(other_tokens),
    )
    assert response.status_code == 403
