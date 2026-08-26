import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions_sync import sync_permissions
from app.modules.auth.dependencies import require_permission
from app.modules.auth.exceptions import InsufficientPermissionsError
from app.modules.auth.repository import AccountRepository, AuthorizationRepository
from app.shared.permissions import PermissionDefinition


def unique_email() -> str:
    return f"role-test-{uuid.uuid4().hex}@example.com"


def unique_permission_code() -> str:
    return f"test.{uuid.uuid4().hex}"


def permission_definition(code: str) -> PermissionDefinition:
    return PermissionDefinition(
        code=code, name="Test permission", resource="test", action="read"
    )


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
    """Bypasses the (admin-gated) HTTP endpoints deliberately — this is
    solving the same bootstrap problem app/core/bootstrap.py solves for the
    real app, just scoped to one test. The JWT issued here stays valid after
    the role is granted, since authorization is checked live against the DB
    on every request, never baked into the token."""
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


async def get_account_id(db: AsyncSession, email: str) -> uuid.UUID:
    account = await AccountRepository(db).get_by_email(email)
    assert account is not None
    return account.id


async def cleanup_permission(db: AsyncSession, code: str) -> None:
    permission = await AuthorizationRepository(db).get_permission_by_code(code)
    if permission is not None:
        await db.delete(permission)
        await db.commit()


# --- role listing -----------------------------------------------------------


async def test_list_roles_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/roles")
    assert response.status_code == 401


async def test_list_roles_requires_admin(client: AsyncClient) -> None:
    _, tokens = await register_and_login(client)
    response = await client.get("/api/v1/auth/roles", headers=auth_headers(tokens))
    assert response.status_code == 403


async def test_admin_can_list_seeded_roles(
    client: AsyncClient, db: AsyncSession
) -> None:
    admin_tokens = await make_admin(client, db)
    response = await client.get(
        "/api/v1/auth/roles", headers=auth_headers(admin_tokens)
    )
    assert response.status_code == 200
    names = {role["name"] for role in response.json()["data"]}
    assert {"buyer", "seller", "admin"} <= names


# --- permission listing ------------------------------------------------------


async def test_list_permissions_requires_admin(client: AsyncClient) -> None:
    _, tokens = await register_and_login(client)
    response = await client.get(
        "/api/v1/auth/permissions", headers=auth_headers(tokens)
    )
    assert response.status_code == 403


async def test_admin_can_list_permissions(
    client: AsyncClient, db: AsyncSession
) -> None:
    admin_tokens = await make_admin(client, db)
    code = unique_permission_code()
    await sync_permissions(db, [permission_definition(code)])
    await db.commit()
    try:
        response = await client.get(
            "/api/v1/auth/permissions", headers=auth_headers(admin_tokens)
        )
        assert response.status_code == 200
        assert code in {p["code"] for p in response.json()["data"]}
    finally:
        await cleanup_permission(db, code)


# --- assigning/revoking a role on an account --------------------------------


async def test_assign_role_to_account_requires_admin(
    client: AsyncClient, db: AsyncSession
) -> None:
    _, non_admin_tokens = await register_and_login(client)
    target_email, _ = await register_and_login(client)
    target_id = await get_account_id(db, target_email)

    response = await client.post(
        f"/api/v1/auth/accounts/{target_id}/roles",
        json={"role_name": "seller"},
        headers=auth_headers(non_admin_tokens),
    )
    assert response.status_code == 403


async def test_admin_can_assign_role_to_account(
    client: AsyncClient, db: AsyncSession
) -> None:
    admin_tokens = await make_admin(client, db)
    target_email, target_tokens = await register_and_login(client)
    target_id = await get_account_id(db, target_email)

    response = await client.post(
        f"/api/v1/auth/accounts/{target_id}/roles",
        json={"role_name": "seller"},
        headers=auth_headers(admin_tokens),
    )
    assert response.status_code == 201

    authz = await client.get(
        "/api/v1/auth/me/authorization", headers=auth_headers(target_tokens)
    )
    assert sorted(authz.json()["data"]["roles"]) == ["buyer", "seller"]


async def test_assigning_unknown_role_is_404(
    client: AsyncClient, db: AsyncSession
) -> None:
    admin_tokens = await make_admin(client, db)
    target_email, _ = await register_and_login(client)
    target_id = await get_account_id(db, target_email)

    response = await client.post(
        f"/api/v1/auth/accounts/{target_id}/roles",
        json={"role_name": "does-not-exist"},
        headers=auth_headers(admin_tokens),
    )
    assert response.status_code == 404


async def test_assigning_role_to_unknown_account_is_404(
    client: AsyncClient, db: AsyncSession
) -> None:
    admin_tokens = await make_admin(client, db)
    response = await client.post(
        f"/api/v1/auth/accounts/{uuid.uuid4()}/roles",
        json={"role_name": "seller"},
        headers=auth_headers(admin_tokens),
    )
    assert response.status_code == 404


async def test_admin_can_revoke_role_from_account(
    client: AsyncClient, db: AsyncSession
) -> None:
    admin_tokens = await make_admin(client, db)
    target_email, target_tokens = await register_and_login(client)
    target_id = await get_account_id(db, target_email)
    admin_headers = auth_headers(admin_tokens)

    await client.post(
        f"/api/v1/auth/accounts/{target_id}/roles",
        json={"role_name": "seller"},
        headers=admin_headers,
    )

    response = await client.delete(
        f"/api/v1/auth/accounts/{target_id}/roles/seller", headers=admin_headers
    )
    assert response.status_code == 200

    authz = await client.get(
        "/api/v1/auth/me/authorization", headers=auth_headers(target_tokens)
    )
    assert authz.json()["data"]["roles"] == ["buyer"]


async def test_list_roles_for_account_requires_admin(
    client: AsyncClient, db: AsyncSession
) -> None:
    target_email, non_admin_tokens = await register_and_login(client)
    target_id = await get_account_id(db, target_email)

    response = await client.get(
        f"/api/v1/auth/accounts/{target_id}/roles",
        headers=auth_headers(non_admin_tokens),
    )
    assert response.status_code == 403


async def test_admin_can_list_an_accounts_roles(
    client: AsyncClient, db: AsyncSession
) -> None:
    admin_tokens = await make_admin(client, db)
    admin_headers = auth_headers(admin_tokens)
    target_email, _ = await register_and_login(client)
    target_id = await get_account_id(db, target_email)

    await client.post(
        f"/api/v1/auth/accounts/{target_id}/roles",
        json={"role_name": "seller"},
        headers=admin_headers,
    )

    response = await client.get(
        f"/api/v1/auth/accounts/{target_id}/roles", headers=admin_headers
    )
    assert response.status_code == 200
    names = sorted(role["name"] for role in response.json()["data"])
    assert names == ["buyer", "seller"]


async def test_listing_roles_for_unknown_account_is_404(
    client: AsyncClient, db: AsyncSession
) -> None:
    admin_tokens = await make_admin(client, db)
    response = await client.get(
        f"/api/v1/auth/accounts/{uuid.uuid4()}/roles",
        headers=auth_headers(admin_tokens),
    )
    assert response.status_code == 404


async def test_list_permissions_for_role_requires_admin(client: AsyncClient) -> None:
    _, tokens = await register_and_login(client)
    response = await client.get(
        "/api/v1/auth/roles/seller/permissions", headers=auth_headers(tokens)
    )
    assert response.status_code == 403


async def test_admin_can_list_a_roles_permissions(
    client: AsyncClient, db: AsyncSession
) -> None:
    admin_tokens = await make_admin(client, db)
    admin_headers = auth_headers(admin_tokens)
    code = unique_permission_code()
    await sync_permissions(db, [permission_definition(code)])
    await db.commit()
    try:
        await client.post(
            "/api/v1/auth/roles/seller/permissions",
            json={"permission_code": code},
            headers=admin_headers,
        )

        response = await client.get(
            "/api/v1/auth/roles/seller/permissions", headers=admin_headers
        )
        assert response.status_code == 200
        assert code in {p["code"] for p in response.json()["data"]}
    finally:
        await client.delete(
            f"/api/v1/auth/roles/seller/permissions/{code}", headers=admin_headers
        )
        await cleanup_permission(db, code)


async def test_listing_permissions_for_unknown_role_is_404(
    client: AsyncClient, db: AsyncSession
) -> None:
    admin_tokens = await make_admin(client, db)
    response = await client.get(
        "/api/v1/auth/roles/does-not-exist/permissions",
        headers=auth_headers(admin_tokens),
    )
    assert response.status_code == 404


# --- assigning/revoking a permission on a role, and it propagating ----------


async def test_admin_can_assign_permission_to_role_and_it_propagates_to_accounts(
    client: AsyncClient, db: AsyncSession
) -> None:
    admin_tokens = await make_admin(client, db)
    admin_headers = auth_headers(admin_tokens)
    target_email, target_tokens = await register_and_login(client)
    target_id = await get_account_id(db, target_email)

    code = unique_permission_code()
    await sync_permissions(db, [permission_definition(code)])
    await db.commit()
    try:
        await client.post(
            f"/api/v1/auth/accounts/{target_id}/roles",
            json={"role_name": "seller"},
            headers=admin_headers,
        )

        assign_response = await client.post(
            "/api/v1/auth/roles/seller/permissions",
            json={"permission_code": code},
            headers=admin_headers,
        )
        assert assign_response.status_code == 201

        authz = await client.get(
            "/api/v1/auth/me/authorization", headers=auth_headers(target_tokens)
        )
        assert code in authz.json()["data"]["permissions"]

        revoke_response = await client.delete(
            f"/api/v1/auth/roles/seller/permissions/{code}", headers=admin_headers
        )
        assert revoke_response.status_code == 200

        authz_after = await client.get(
            "/api/v1/auth/me/authorization", headers=auth_headers(target_tokens)
        )
        assert code not in authz_after.json()["data"]["permissions"]
    finally:
        await client.delete(
            f"/api/v1/auth/accounts/{target_id}/roles/seller", headers=admin_headers
        )
        await cleanup_permission(db, code)


async def test_assigning_permission_to_unknown_role_is_404(
    client: AsyncClient, db: AsyncSession
) -> None:
    admin_tokens = await make_admin(client, db)
    code = unique_permission_code()
    await sync_permissions(db, [permission_definition(code)])
    await db.commit()
    try:
        response = await client.post(
            "/api/v1/auth/roles/does-not-exist/permissions",
            json={"permission_code": code},
            headers=auth_headers(admin_tokens),
        )
        assert response.status_code == 404
    finally:
        await cleanup_permission(db, code)


async def test_assigning_unknown_permission_to_role_is_404(
    client: AsyncClient, db: AsyncSession
) -> None:
    admin_tokens = await make_admin(client, db)
    response = await client.post(
        "/api/v1/auth/roles/seller/permissions",
        json={"permission_code": "does.not.exist"},
        headers=auth_headers(admin_tokens),
    )
    assert response.status_code == 404


# --- proves require_permission itself enforces correctly --------------------
# No production route uses require_permission yet (the catalog is empty), so
# this exercises the dependency function directly: the exact reusable piece
# other modules will call `Depends(require_permission(...))` with.


async def test_require_permission_dependency_denies_then_grants_after_assignment(
    client: AsyncClient, db: AsyncSession
) -> None:
    admin_tokens = await make_admin(client, db)
    admin_headers = auth_headers(admin_tokens)
    target_email, _ = await register_and_login(client)
    target_id = await get_account_id(db, target_email)

    code = unique_permission_code()
    await sync_permissions(db, [permission_definition(code)])
    await db.commit()
    dependency = require_permission(code)
    try:
        await client.post(
            f"/api/v1/auth/accounts/{target_id}/roles",
            json={"role_name": "seller"},
            headers=admin_headers,
        )
        target_account = await AccountRepository(db).get_by_id(target_id)
        assert target_account is not None

        with pytest.raises(InsufficientPermissionsError):
            await dependency(account=target_account, db=db)

        await client.post(
            "/api/v1/auth/roles/seller/permissions",
            json={"permission_code": code},
            headers=admin_headers,
        )

        result = await dependency(account=target_account, db=db)
        assert result.id == target_account.id
    finally:
        await client.delete(
            f"/api/v1/auth/roles/seller/permissions/{code}", headers=admin_headers
        )
        await client.delete(
            f"/api/v1/auth/accounts/{target_id}/roles/seller", headers=admin_headers
        )
        await cleanup_permission(db, code)
