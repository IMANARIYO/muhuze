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
    return f"direct-perm-test-{uuid.uuid4().hex}@example.com"


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


async def test_grant_direct_permission_requires_admin(
    client: AsyncClient, db: AsyncSession
) -> None:
    _, non_admin_tokens = await register_and_login(client)
    target_email, _ = await register_and_login(client)
    target_id = await get_account_id(db, target_email)

    response = await client.post(
        f"/api/v1/auth/accounts/{target_id}/permissions",
        json={"permission_code": "whatever"},
        headers=auth_headers(non_admin_tokens),
    )
    assert response.status_code == 403


async def test_admin_can_grant_direct_permission_without_any_role(
    client: AsyncClient, db: AsyncSession
) -> None:
    """A plain buyer (no seller/admin role) gets a permission directly —
    proves permissions don't require a role to reach an account."""
    admin_tokens = await make_admin(client, db)
    target_email, target_tokens = await register_and_login(client)
    target_id = await get_account_id(db, target_email)

    code = unique_permission_code()
    await sync_permissions(db, [permission_definition(code)])
    await db.commit()
    try:
        grant_response = await client.post(
            f"/api/v1/auth/accounts/{target_id}/permissions",
            json={"permission_code": code},
            headers=auth_headers(admin_tokens),
        )
        assert grant_response.status_code == 201

        authz = await client.get(
            "/api/v1/auth/me/authorization", headers=auth_headers(target_tokens)
        )
        assert authz.json()["data"]["roles"] == ["buyer"]
        assert code in authz.json()["data"]["permissions"]
    finally:
        await client.delete(
            f"/api/v1/auth/accounts/{target_id}/permissions/{code}",
            headers=auth_headers(admin_tokens),
        )
        await cleanup_permission(db, code)


async def test_direct_permission_survives_role_removal(
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
        await client.post(
            f"/api/v1/auth/accounts/{target_id}/permissions",
            json={"permission_code": code},
            headers=admin_headers,
        )

        await client.delete(
            f"/api/v1/auth/accounts/{target_id}/roles/seller", headers=admin_headers
        )

        authz = await client.get(
            "/api/v1/auth/me/authorization", headers=auth_headers(target_tokens)
        )
        assert authz.json()["data"]["roles"] == ["buyer"]
        assert code in authz.json()["data"]["permissions"]
    finally:
        await client.delete(
            f"/api/v1/auth/accounts/{target_id}/permissions/{code}",
            headers=admin_headers,
        )
        await cleanup_permission(db, code)


async def test_effective_permissions_dedupes_role_and_direct_source(
    client: AsyncClient, db: AsyncSession
) -> None:
    """Same permission granted both via role and directly shows up once,
    not twice, in effective permissions."""
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
        await client.post(
            "/api/v1/auth/roles/seller/permissions",
            json={"permission_code": code},
            headers=admin_headers,
        )
        await client.post(
            f"/api/v1/auth/accounts/{target_id}/permissions",
            json={"permission_code": code},
            headers=admin_headers,
        )

        authz = await client.get(
            "/api/v1/auth/me/authorization", headers=auth_headers(target_tokens)
        )
        permissions = authz.json()["data"]["permissions"]
        assert permissions.count(code) == 1
    finally:
        await client.delete(
            f"/api/v1/auth/roles/seller/permissions/{code}", headers=admin_headers
        )
        await client.delete(
            f"/api/v1/auth/accounts/{target_id}/permissions/{code}",
            headers=admin_headers,
        )
        await client.delete(
            f"/api/v1/auth/accounts/{target_id}/roles/seller", headers=admin_headers
        )
        await cleanup_permission(db, code)


async def test_revoke_direct_permission(client: AsyncClient, db: AsyncSession) -> None:
    admin_tokens = await make_admin(client, db)
    admin_headers = auth_headers(admin_tokens)
    target_email, target_tokens = await register_and_login(client)
    target_id = await get_account_id(db, target_email)

    code = unique_permission_code()
    await sync_permissions(db, [permission_definition(code)])
    await db.commit()
    try:
        await client.post(
            f"/api/v1/auth/accounts/{target_id}/permissions",
            json={"permission_code": code},
            headers=admin_headers,
        )

        revoke_response = await client.delete(
            f"/api/v1/auth/accounts/{target_id}/permissions/{code}",
            headers=admin_headers,
        )
        assert revoke_response.status_code == 200

        authz = await client.get(
            "/api/v1/auth/me/authorization", headers=auth_headers(target_tokens)
        )
        assert code not in authz.json()["data"]["permissions"]
    finally:
        await cleanup_permission(db, code)


async def test_grant_unknown_permission_directly_is_404(
    client: AsyncClient, db: AsyncSession
) -> None:
    admin_tokens = await make_admin(client, db)
    target_email, _ = await register_and_login(client)
    target_id = await get_account_id(db, target_email)

    response = await client.post(
        f"/api/v1/auth/accounts/{target_id}/permissions",
        json={"permission_code": "does.not.exist"},
        headers=auth_headers(admin_tokens),
    )
    assert response.status_code == 404


async def test_grant_direct_permission_to_unknown_account_is_404(
    client: AsyncClient, db: AsyncSession
) -> None:
    admin_tokens = await make_admin(client, db)
    code = unique_permission_code()
    await sync_permissions(db, [permission_definition(code)])
    await db.commit()
    try:
        response = await client.post(
            f"/api/v1/auth/accounts/{uuid.uuid4()}/permissions",
            json={"permission_code": code},
            headers=auth_headers(admin_tokens),
        )
        assert response.status_code == 404
    finally:
        await cleanup_permission(db, code)


async def test_admin_can_list_an_accounts_direct_permissions(
    client: AsyncClient, db: AsyncSession
) -> None:
    admin_tokens = await make_admin(client, db)
    admin_headers = auth_headers(admin_tokens)
    target_email, _ = await register_and_login(client)
    target_id = await get_account_id(db, target_email)

    code = unique_permission_code()
    await sync_permissions(db, [permission_definition(code)])
    await db.commit()
    try:
        await client.post(
            f"/api/v1/auth/accounts/{target_id}/permissions",
            json={"permission_code": code},
            headers=admin_headers,
        )

        response = await client.get(
            f"/api/v1/auth/accounts/{target_id}/permissions", headers=admin_headers
        )
        assert response.status_code == 200
        assert response.json()["data"] == [code]
    finally:
        await client.delete(
            f"/api/v1/auth/accounts/{target_id}/permissions/{code}",
            headers=admin_headers,
        )
        await cleanup_permission(db, code)


async def test_require_permission_dependency_grants_via_direct_permission_alone(
    client: AsyncClient, db: AsyncSession
) -> None:
    """No role at all — proves require_permission checks direct grants,
    not just role-derived ones."""
    admin_tokens = await make_admin(client, db)
    admin_headers = auth_headers(admin_tokens)
    target_email, _ = await register_and_login(client)
    target_id = await get_account_id(db, target_email)

    code = unique_permission_code()
    await sync_permissions(db, [permission_definition(code)])
    await db.commit()
    dependency = require_permission(code)
    try:
        target_account = await AccountRepository(db).get_by_id(target_id)
        assert target_account is not None

        with pytest.raises(InsufficientPermissionsError):
            await dependency(account=target_account, db=db)

        await client.post(
            f"/api/v1/auth/accounts/{target_id}/permissions",
            json={"permission_code": code},
            headers=admin_headers,
        )

        result = await dependency(account=target_account, db=db)
        assert result.id == target_account.id
    finally:
        await client.delete(
            f"/api/v1/auth/accounts/{target_id}/permissions/{code}",
            headers=admin_headers,
        )
        await cleanup_permission(db, code)
