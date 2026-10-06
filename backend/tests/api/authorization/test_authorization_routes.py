"""Roles and permissions through the HTTP API, against a real PostgreSQL database."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.bootstrap import run_startup_tasks
from app.core.permission_registry import ALL_PERMISSIONS
from app.core.permissions import PermissionDefinition
from app.main import create_app
from app.modules.auth.auth_model import Account
from app.modules.authorization.authorization_model import AccountRole, Permission, Role
from app.modules.authorization.authorization_service import AuthorizationService
from app.shared.responses.pagination import PaginationParams

API = "/api/v1"
PASSWORD = "correct-horse-battery"
ALL_CODES = sorted(permission.code for permission in ALL_PERMISSIONS)
# What the seller role receives by default from the real catalog.
SELLER_DEFAULT_CODES = sorted(
    permission.code for permission in ALL_PERMISSIONS if "seller" in permission.default_roles
)


@pytest.fixture
def role_id(db_client: AsyncClient, admin):
    async def _role_id(name: str) -> str:
        page = (await db_client.get(f"{API}/roles", headers=admin.headers)).json()["data"]
        return next(role["id"] for role in page["items"] if role["name"] == name)

    return _role_id


@pytest.fixture
def create_role(db_client: AsyncClient, admin):
    async def _create_role(name: str = "support") -> str:
        response = await db_client.post(f"{API}/roles", json={"name": name}, headers=admin.headers)
        assert response.status_code == 201, response.text
        return response.json()["data"]["id"]

    return _create_role


# ── The caller's own access ──────────────────────────────────────────────


async def test_a_new_account_is_a_buyer_with_no_permissions(db_client: AsyncClient, user) -> None:
    response = await db_client.get(f"{API}/authorization/me", headers=user.headers)

    assert response.status_code == 200
    assert response.json()["data"] == {"roles": ["buyer"], "permissions": []}


async def test_an_admin_holds_every_permission(db_client: AsyncClient, admin) -> None:
    response = await db_client.get(f"{API}/authorization/me", headers=admin.headers)

    assert response.json()["data"] == {"roles": ["admin", "buyer"], "permissions": ALL_CODES}


async def test_authorization_me_requires_login(db_client: AsyncClient) -> None:
    assert (await db_client.get(f"{API}/authorization/me")).status_code == 401


# ── Access control ───────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/roles"),
        ("POST", "/roles"),
        ("GET", "/permissions"),
        ("GET", "/roles/{id}"),
        ("PATCH", "/roles/{id}"),
        ("DELETE", "/roles/{id}"),
        ("GET", "/roles/{id}/permissions"),
        ("PUT", "/roles/{id}/permissions/role.read"),
        ("DELETE", "/roles/{id}/permissions/role.read"),
        ("GET", "/accounts/{id}/roles"),
        ("PUT", "/accounts/{id}/roles/{id}"),
        ("DELETE", "/accounts/{id}/roles/{id}"),
        ("GET", "/accounts/{id}/permissions"),
        ("PUT", "/accounts/{id}/permissions/role.read"),
        ("DELETE", "/accounts/{id}/permissions/role.read"),
    ],
)
async def test_every_management_endpoint_is_closed_to_ordinary_accounts(
    db_client: AsyncClient, user, method: str, path: str
) -> None:
    url = API + path.replace("{id}", user.id)
    body = {"json": {"name": "sneaky"}} if method in ("POST", "PATCH") else {}

    anonymous = await db_client.request(method, url, **body)
    ordinary = await db_client.request(method, url, headers=user.headers, **body)

    assert anonymous.status_code == 401
    assert ordinary.status_code == 403
    assert ordinary.json() == {
        "success": False,
        "data": None,
        "message": "You do not have permission to perform this action",
        "status_code": 403,
    }


# ── Roles ────────────────────────────────────────────────────────────────


async def test_the_three_system_roles_exist(db_client: AsyncClient, admin) -> None:
    response = await db_client.get(f"{API}/roles", headers=admin.headers)

    assert response.status_code == 200
    page = response.json()["data"]
    assert page["total"] == 3
    assert [role["name"] for role in page["items"]] == ["admin", "buyer", "seller"]
    assert all(role["is_system"] for role in page["items"])


async def test_roles_are_paginated(db_client: AsyncClient, admin) -> None:
    response = await db_client.get(
        f"{API}/roles", params={"page": 2, "page_size": 2}, headers=admin.headers
    )

    page = response.json()["data"]
    assert [role["name"] for role in page["items"]] == ["seller"]
    assert (page["page"], page["page_size"], page["total"], page["total_pages"]) == (2, 2, 3, 2)


async def test_create_role(db_client: AsyncClient, admin) -> None:
    response = await db_client.post(
        f"{API}/roles",
        json={"name": "  Support_Agent ", "description": "Answers customers"},
        headers=admin.headers,
    )

    assert response.status_code == 201
    role = response.json()["data"]
    assert role["name"] == "support_agent"  # trimmed and lowercased
    assert role["description"] == "Answers customers"
    assert role["is_system"] is False

    fetched = await db_client.get(f"{API}/roles/{role['id']}", headers=admin.headers)
    assert fetched.json()["data"] == role


@pytest.mark.parametrize("name", ["a", "Has Space", "9lives", "semi;colon", "x" * 51])
async def test_create_role_rejects_bad_names(db_client: AsyncClient, admin, name: str) -> None:
    response = await db_client.post(f"{API}/roles", json={"name": name}, headers=admin.headers)
    assert response.status_code == 422


async def test_role_names_are_unique(db_client: AsyncClient, admin, create_role) -> None:
    await create_role("support")

    duplicate = await db_client.post(
        f"{API}/roles", json={"name": "SUPPORT"}, headers=admin.headers
    )
    system = await db_client.post(f"{API}/roles", json={"name": "admin"}, headers=admin.headers)

    assert duplicate.status_code == system.status_code == 409
    assert duplicate.json()["message"] == "A role with this name already exists"


async def test_update_role(db_client: AsyncClient, admin, create_role) -> None:
    support = await create_role("support")
    await create_role("finance")

    renamed = await db_client.patch(
        f"{API}/roles/{support}", json={"name": "helpdesk"}, headers=admin.headers
    )
    described = await db_client.patch(
        f"{API}/roles/{support}", json={"description": "Front line"}, headers=admin.headers
    )
    taken = await db_client.patch(
        f"{API}/roles/{support}", json={"name": "finance"}, headers=admin.headers
    )

    assert renamed.json()["data"]["name"] == "helpdesk"
    # Only the fields that were sent change.
    assert described.json()["data"]["name"] == "helpdesk"
    assert described.json()["data"]["description"] == "Front line"
    assert taken.status_code == 409


async def test_system_roles_cannot_be_renamed_or_deleted(
    db_client: AsyncClient, admin, role_id
) -> None:
    seller = await role_id("seller")

    renamed = await db_client.patch(
        f"{API}/roles/{seller}", json={"name": "merchant"}, headers=admin.headers
    )
    deleted = await db_client.delete(f"{API}/roles/{seller}", headers=admin.headers)
    described = await db_client.patch(
        f"{API}/roles/{seller}", json={"description": "Sells things"}, headers=admin.headers
    )

    assert renamed.status_code == deleted.status_code == 422
    assert renamed.json()["message"] == "System roles cannot be renamed or deleted"
    assert described.status_code == 200  # the description is not protected
    assert described.json()["data"]["name"] == "seller"


async def test_delete_role_takes_its_access_away(
    db_client: AsyncClient, admin, user, create_role
) -> None:
    support = await create_role()
    await db_client.put(f"{API}/roles/{support}/permissions/role.read", headers=admin.headers)
    await db_client.put(f"{API}/accounts/{user.id}/roles/{support}", headers=admin.headers)
    assert (await db_client.get(f"{API}/roles", headers=user.headers)).status_code == 200

    deleted = await db_client.delete(f"{API}/roles/{support}", headers=admin.headers)

    assert deleted.status_code == 200
    assert (await db_client.get(f"{API}/roles", headers=user.headers)).status_code == 403
    assert (await db_client.get(f"{API}/roles/{support}", headers=admin.headers)).status_code == 404
    again = await db_client.delete(f"{API}/roles/{support}", headers=admin.headers)
    assert again.status_code == 404


# ── Permissions ──────────────────────────────────────────────────────────


async def test_permission_catalog_is_listed_and_filtered(db_client: AsyncClient, admin) -> None:
    everything = await db_client.get(f"{API}/permissions", headers=admin.headers)
    roles_only = await db_client.get(
        f"{API}/permissions", params={"resource": "role"}, headers=admin.headers
    )

    assert [p["code"] for p in everything.json()["data"]["items"]] == ALL_CODES
    role_permissions = roles_only.json()["data"]["items"]
    assert [p["code"] for p in role_permissions] == ["role.assign", "role.manage", "role.read"]
    assert role_permissions[0]["resource"] == "role"
    assert role_permissions[0]["action"] == "assign"


async def test_a_role_passes_its_permissions_to_the_accounts_holding_it(
    db_client: AsyncClient, admin, user, create_role
) -> None:
    support = await create_role()

    added = await db_client.put(
        f"{API}/roles/{support}/permissions/role.read", headers=admin.headers
    )
    repeated = await db_client.put(
        f"{API}/roles/{support}/permissions/role.read", headers=admin.headers
    )
    granted = await db_client.put(
        f"{API}/accounts/{user.id}/roles/{support}", headers=admin.headers
    )

    assert added.status_code == repeated.status_code == granted.status_code == 200
    carried = await db_client.get(f"{API}/roles/{support}/permissions", headers=admin.headers)
    assert [p["code"] for p in carried.json()["data"]["items"]] == ["role.read"]
    mine = (await db_client.get(f"{API}/authorization/me", headers=user.headers)).json()["data"]
    assert mine == {"roles": ["buyer", "support"], "permissions": ["role.read"]}
    # The permission works, and only that one.
    assert (await db_client.get(f"{API}/roles", headers=user.headers)).status_code == 200
    assert (await db_client.get(f"{API}/permissions", headers=user.headers)).status_code == 403

    removed = await db_client.delete(
        f"{API}/roles/{support}/permissions/role.read", headers=admin.headers
    )
    assert removed.status_code == 200
    assert (await db_client.get(f"{API}/roles", headers=user.headers)).status_code == 403


async def test_the_admin_roles_permissions_cannot_be_changed(
    db_client: AsyncClient, admin, role_id
) -> None:
    admin_role = await role_id("admin")
    url = f"{API}/roles/{admin_role}/permissions/role.read"

    removed = await db_client.delete(url, headers=admin.headers)
    added = await db_client.put(url, headers=admin.headers)

    assert removed.status_code == added.status_code == 422
    assert removed.json()["message"] == "The admin role always holds every permission"
    assert (await db_client.get(f"{API}/roles", headers=admin.headers)).status_code == 200


async def test_unknown_roles_permissions_and_accounts_are_not_found(
    db_client: AsyncClient, admin, user, create_role
) -> None:
    support = await create_role()
    missing = uuid.uuid4()
    urls = [
        f"{API}/roles/{support}/permissions/product.teleport",
        f"{API}/roles/{missing}/permissions/role.read",
        f"{API}/accounts/{user.id}/roles/{missing}",
        f"{API}/accounts/{missing}/roles/{support}",
        f"{API}/accounts/{user.id}/permissions/product.teleport",
        f"{API}/accounts/{missing}/permissions/role.read",
    ]

    for url in urls:
        response = await db_client.put(url, headers=admin.headers)
        assert response.status_code == 404, url

    not_found = await db_client.get(f"{API}/accounts/{missing}/roles", headers=admin.headers)
    assert not_found.json()["message"] == "Account not found"


# ── Roles and direct permissions of an account ───────────────────────────


async def test_roles_of_an_account_are_granted_listed_and_revoked(
    db_client: AsyncClient, admin, user, role_id, session_factory
) -> None:
    seller = await role_id("seller")
    url = f"{API}/accounts/{user.id}/roles/{seller}"

    assert (await db_client.put(url, headers=admin.headers)).status_code == 200
    assert (await db_client.put(url, headers=admin.headers)).status_code == 200  # idempotent

    listed = await db_client.get(f"{API}/accounts/{user.id}/roles", headers=admin.headers)
    assert [role["name"] for role in listed.json()["data"]["items"]] == ["buyer", "seller"]
    async with session_factory() as session:
        grant = await session.scalar(
            select(AccountRole).where(
                AccountRole.account_id == uuid.UUID(user.id),
                AccountRole.role_id == uuid.UUID(seller),
            )
        )
    assert str(grant.granted_by_account_id) == admin.id  # who granted it is recorded

    assert (await db_client.delete(url, headers=admin.headers)).status_code == 200
    listed = await db_client.get(f"{API}/accounts/{user.id}/roles", headers=admin.headers)
    assert [role["name"] for role in listed.json()["data"]["items"]] == ["buyer"]


async def test_a_permission_can_be_granted_directly_to_one_account(
    db_client: AsyncClient, admin, user
) -> None:
    url = f"{API}/accounts/{user.id}/permissions/permission.read"

    assert (await db_client.put(url, headers=admin.headers)).status_code == 200

    mine = (await db_client.get(f"{API}/authorization/me", headers=user.headers)).json()["data"]
    assert mine == {"roles": ["buyer"], "permissions": ["permission.read"]}
    assert (await db_client.get(f"{API}/permissions", headers=user.headers)).status_code == 200
    direct = await db_client.get(f"{API}/accounts/{user.id}/permissions", headers=admin.headers)
    assert [p["code"] for p in direct.json()["data"]["items"]] == ["permission.read"]

    assert (await db_client.delete(url, headers=admin.headers)).status_code == 200
    assert (await db_client.get(f"{API}/permissions", headers=user.headers)).status_code == 403


async def test_direct_permissions_list_excludes_those_held_through_roles(
    db_client: AsyncClient, admin
) -> None:
    response = await db_client.get(f"{API}/accounts/{admin.id}/permissions", headers=admin.headers)

    assert response.json()["data"]["total"] == 0


async def test_an_admin_cannot_remove_their_own_admin_role(
    db_client: AsyncClient, admin, sign_up, role_id
) -> None:
    admin_role = await role_id("admin")
    other_admin = await sign_up("second-admin@example.com", "admin")

    own = await db_client.delete(
        f"{API}/accounts/{admin.id}/roles/{admin_role}", headers=admin.headers
    )
    other = await db_client.delete(
        f"{API}/accounts/{other_admin.id}/roles/{admin_role}", headers=admin.headers
    )

    assert own.status_code == 422
    assert own.json()["message"] == "You cannot remove the admin role from your own account"
    assert other.status_code == 200
    # The demoted admin loses access at once, with the token they already hold.
    assert (await db_client.get(f"{API}/roles", headers=other_admin.headers)).status_code == 403


# ── Catalog sync and bootstrap (what happens at startup) ─────────────────


async def test_sync_adds_new_permissions_and_removes_retired_ones(session_factory) -> None:
    report_view = PermissionDefinition(
        code="report.view",
        name="View reports",
        description="See reports.",
        default_roles=("seller",),
    )
    everything = PaginationParams(page_size=100)

    async with session_factory() as session:
        service = AuthorizationService(session)

        async def codes_of(role_name: str) -> list[str]:
            role = await session.scalar(select(Role).where(Role.name == role_name))
            page = await service.list_role_permissions(role.id, everything)
            return [permission.code for permission in page.items]

        # New in the code: given to its default role, and to admin.
        await service.sync_permissions([*ALL_PERMISSIONS, report_view])
        assert await codes_of("seller") == sorted([*SELLER_DEFAULT_CODES, "report.view"])
        assert await codes_of("admin") == sorted([*ALL_CODES, "report.view"])

        # An admin takes it away from sellers; the next startup must not put it back.
        seller = await session.scalar(select(Role).where(Role.name == "seller"))
        await service.remove_permission_from_role(seller.id, "report.view", changed_by=uuid.uuid4())
        await service.sync_permissions([*ALL_PERMISSIONS, report_view])
        assert await codes_of("seller") == SELLER_DEFAULT_CODES
        assert "report.view" in await codes_of("admin")

        # Retired from the code: gone from the table and from every role.
        await service.sync_permissions(ALL_PERMISSIONS)
        assert await codes_of("admin") == ALL_CODES
        stored = await session.scalars(select(Permission.code))
        assert sorted(stored) == ALL_CODES


async def test_startup_creates_the_first_admin_once(
    make_settings, session_factory, email_outbox, db_client: AsyncClient
) -> None:
    settings = make_settings(
        bootstrap_admin_email="Root@Example.com", bootstrap_admin_password="a-long-root-password"
    )
    app = create_app(settings)
    app.state.session_factory = session_factory
    app.state.email_sender = email_outbox

    await run_startup_tasks(app)
    await run_startup_tasks(app)  # a restart changes nothing

    async with session_factory() as session:
        accounts = list(
            await session.scalars(select(Account).where(Account.email == "root@example.com"))
        )
        authorization = await AuthorizationService(session).get_account_authorization(
            accounts[0].id
        )
    assert len(accounts) == 1
    assert accounts[0].is_verified is True
    assert authorization.roles == ["admin", "buyer"]
    assert authorization.permissions == ALL_CODES
    assert email_outbox.sent == []  # no verification email for a system-created account

    logged_in = await db_client.post(
        f"{API}/auth/login",
        json={"email": "root@example.com", "password": "a-long-root-password"},
    )
    assert logged_in.status_code == 200


async def test_startup_never_resets_an_existing_accounts_password(
    make_settings, session_factory, email_outbox, db_client: AsyncClient, user
) -> None:
    settings = make_settings(
        bootstrap_admin_email="user@example.com", bootstrap_admin_password="a-different-password"
    )
    app = create_app(settings)
    app.state.session_factory = session_factory
    app.state.email_sender = email_outbox

    await run_startup_tasks(app)

    # The existing account becomes an admin but keeps its own password.
    mine = (await db_client.get(f"{API}/authorization/me", headers=user.headers)).json()["data"]
    assert "admin" in mine["roles"]
    old = await db_client.post(
        f"{API}/auth/login", json={"email": "user@example.com", "password": PASSWORD}
    )
    new = await db_client.post(
        f"{API}/auth/login",
        json={"email": "user@example.com", "password": "a-different-password"},
    )
    assert old.status_code == 200
    assert new.status_code == 401
