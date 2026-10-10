# 003 — Roles and Permissions

**Status:** `TESTING`. Code, migration, tests, and docs are written. The test suite has not been run yet (see [Progress](#progress)).

Business rules: [`README.md` §5.4](../../../README.md#54-authorization-and-ownership). API contract: [`docs/api/roles_and_permissions.md`](../api/roles_and_permissions.md). Tables: [`docs/database/database_schema.dbml`](../database/database_schema.dbml).

## Purpose

Decide what each account is allowed to do. Authentication (001) answers *who are you?*; this feature answers *may you do this kind of thing?* Every later feature protects its endpoints with it.

## Concepts

| Thing | What it is | Who controls it |
|---|---|---|
| **Permission** | One allowed action, named `<resource>.<action>` (`product.create`, `role.manage`) | **The code.** Each feature declares its own. Admins can assign permissions but never create or edit them. |
| **Role** | A named bundle of permissions (`buyer`, `seller`, `admin`, `support`, …) | **Admins.** Roles are data: they can be created, renamed, and deleted. |
| **Direct grant** | One permission given to one account, outside any role | Admins, for exceptions. |

**An account's permissions = the permissions of all its roles + its direct grants.** There is no "deny": access is only ever added.

## Rules

**System roles**

- Three roles are created by the migration: `buyer`, `seller`, `admin`. They cannot be renamed or deleted. Their description can be edited.
- **`buyer`** is given to every account at registration (README §6.2: every account can buy).
- **`seller`** will be given when a seller application is approved (feature 004). The role marks "has been approved"; whether a seller may trade *right now* is the seller's status, checked separately.
- **`admin`** always holds **every** permission. New permissions are added to it automatically at startup, and its permissions cannot be edited.

**Permissions**

- Defined in code only, in each feature's `<feature>_permissions.py`, and synced into the `permissions` table at startup.
- A permission may name **default roles**. It is given to them once, when it first appears. After that, admins decide: a later startup never re-adds or removes a role's permissions (except `admin`, which always has all).
- A permission removed from the code is deleted at the next startup, together with every grant of it.

**Safety rules**

- An admin cannot remove the `admin` role from their own account. Another admin can.
- A permission never grants access to *someone else's* resource. Ownership is checked in each feature's service (AGENTS.md §12).
- Changes take effect on the next request. Permissions are read from the database every time, not stored in the access token.

**The first admin**

- If `BOOTSTRAP_ADMIN_EMAIL` and `BOOTSTRAP_ADMIN_PASSWORD` are set, startup makes sure that account exists, is verified, and holds `admin`.
- If the account already exists it only receives the role. Its password is never reset.
- With both variables empty, no admin is created.

## Permissions owned by this feature

| Code | Allows | Default roles |
|---|---|---|
| `role.read` | See roles, what they carry, and which accounts hold them | – |
| `role.manage` | Create, rename, delete roles; change a role's permissions | – |
| `role.assign` | Give a role to an account, or take it away | – |
| `permission.read` | See the permission catalog and an account's direct grants | – |
| `permission.grant` | Grant a permission directly to an account, or revoke it | – |

None has a default role, so only `admin` can manage access until an admin decides otherwise.

`role.assign` and `permission.grant` are powerful: whoever holds them can give themselves or anyone else more access, including `admin`. Assign them with care.

## How a feature uses it

**1. Declare the permissions** in `app/modules/products/product_permissions.py`:

```python
PRODUCT_CREATE = PermissionDefinition(
    code="product.create",
    name="Create products",
    description="Add a new product to the seller's own shop.",
    default_roles=("seller",),
)
PRODUCT_PERMISSIONS = (PRODUCT_CREATE,)
```

**2. Register them** by adding `*PRODUCT_PERMISSIONS` to `ALL_PERMISSIONS` in `app/core/permission_registry.py`.

**3. Protect the endpoint:**

```python
@product_router.post("/products")
async def create_product(
    account: Annotated[Account, Depends(require_permission(PRODUCT_CREATE))], ...
): ...
```

`401` without a valid token, `403` without the permission. No migration is needed for a new permission: the next startup adds it.

**From a service**, another feature calls `AuthorizationService.assign_role(...)` (for example, sellers granting `seller` on approval). That method does not commit, so it joins the caller's transaction.

## Design

```
app/modules/authorization/
├── authorization_routes.py        # paths, schemas, status codes
├── authorization_dependencies.py  # require_permission, get_authorization_service
├── authorization_service.py       # every rule above; catalog sync
├── authorization_repository.py    # queries only
├── authorization_model.py         # Role, Permission, AccountRole, RolePermission, AccountPermission
├── authorization_permissions.py   # this feature's own permissions
├── authorization_schema.py
├── authorization_exceptions.py
└── authorization_constants.py     # SystemRole
```

| Supporting file | Role |
|---|---|
| `app/core/permissions.py` | `PermissionDefinition`: how a feature declares a permission |
| `app/core/permission_registry.py` | `ALL_PERMISSIONS`: every feature's permissions |
| `app/bootstrap.py` | Startup tasks: catalog sync, then the first admin |
| `migrations/versions/…0002…` | The five tables, the three system roles, and `buyer` for existing accounts |

The module is named `authorization` (not `roles` or `permissions`) because it owns both, and because `<feature>_permissions.py` is already the name of the file where *any* feature lists its permissions.

**Dependencies between features.** `auth` uses `AuthorizationService` to give `buyer` at registration. `authorization` never imports the auth service; where an endpoint needs "does this account exist?", the route dependency asks `AuthService`. This keeps the two services free of a circular import.

## Security review

- [x] Every management endpoint requires a specific permission; ordinary accounts get `403`, anonymous callers `401` (tested for all 15 endpoints).
- [x] The permission check runs before the target account is looked up, so a caller without access can't learn whether an account id exists.
- [x] Permissions cannot be created or edited through the API; only codes from the catalog are accepted.
- [x] System roles are protected; the `admin` role cannot be stripped of permissions.
- [x] An admin cannot remove their own `admin` role.
- [x] Who granted a role or a direct permission is recorded (`granted_by_account_id`), and every change is logged with the acting account.
- [x] The bootstrap password is a secret setting, at least 12 characters, and never overwrites an existing account's password.

## Known gaps

| Gap | Risk | Planned with |
|---|---|---|
| The last admin can still be removed by *another* admin, leaving one; and nothing prevents every admin being suspended | Lock-out. Recoverable through the bootstrap variables | Revisit with `015_admin` |
| No list of "accounts holding role X" | Admin UI can't show a role's members | `002_users` / `015_admin` (account directory) |
| Permissions are read from the database on every protected request | One extra query per request | Cache if it ever shows up in profiling |
| Role and permission changes are logged, but there is no audit table | History lives only in logs | `015_admin` |

## Progress

- [x] Requirements and rules (this document, README §5.4)
- [x] Database design and migration `0002`
- [x] Models, repository, service, schemas, routes, dependencies
- [x] Catalog sync and first-admin bootstrap at startup
- [x] `buyer` given at registration, and to accounts that already existed
- [x] Tests written: `tests/api/authorization/`
- [x] API and feature documentation
- [ ] **Tests run and passing** (run by the user: `cd backend && .venv/Scripts/python -m pytest -q`)
