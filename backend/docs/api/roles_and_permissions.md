# Roles and Permissions API

**Status:** implemented (`app/modules/authorization/`). Rules and rationale: [`docs/features/003_roles_and_permissions.md`](../features/003_roles_and_permissions.md).

All paths are under `/api/v1`. Every endpoint needs `Authorization: Bearer <access token>` and uses the [standard envelope](response-format.md). List endpoints return a `Page` and accept `page` and `page_size`.

## For the frontend

Call `GET /authorization/me` after login and keep the result:

```json
{ "roles": ["buyer", "seller"], "permissions": ["product.create", "product.update"] }
```

Decide what to show from `permissions`, never from role names: `can('product.create')`, not `role === 'seller'`. Admins can create new roles at any time, and a role created tomorrow must work without a frontend change. Hiding a button is not security; the API checks every request.

Permissions are read live, so a change made by an admin applies to the user's next request. Fetch `/authorization/me` again when the app regains focus or after a `403`.

## Endpoints

| Method | Path | Needs | Purpose |
|---|---|---|---|
| GET | `/authorization/me` | login | The caller's roles and permissions |
| GET | `/roles` | `role.read` | All roles, by name |
| POST | `/roles` | `role.manage` | Create a role (201) |
| GET | `/roles/{role_id}` | `role.read` | One role |
| PATCH | `/roles/{role_id}` | `role.manage` | Change name and/or description |
| DELETE | `/roles/{role_id}` | `role.manage` | Delete a role |
| GET | `/permissions` | `permission.read` | The permission catalog, by code. Filter: `resource` |
| GET | `/roles/{role_id}/permissions` | `role.read` | Permissions a role carries |
| PUT | `/roles/{role_id}/permissions/{code}` | `role.manage` | Add a permission to a role |
| DELETE | `/roles/{role_id}/permissions/{code}` | `role.manage` | Remove a permission from a role |
| GET | `/accounts/{account_id}/roles` | `role.read` | Roles an account holds |
| PUT | `/accounts/{account_id}/roles/{role_id}` | `role.assign` | Give a role to an account |
| DELETE | `/accounts/{account_id}/roles/{role_id}` | `role.assign` | Take a role from an account |
| GET | `/accounts/{account_id}/permissions` | `permission.read` | Permissions granted **directly** to an account (not those from roles) |
| PUT | `/accounts/{account_id}/permissions/{code}` | `permission.grant` | Grant a permission directly |
| DELETE | `/accounts/{account_id}/permissions/{code}` | `permission.grant` | Revoke a direct grant |

`PUT` and `DELETE` are safe to repeat: granting something already granted, or revoking something not held, returns `200`.

## Bodies and objects

**Create / update a role**

```json
{ "name": "support_agent", "description": "Answers customers" }
```

`name`: 2 to 50 lowercase letters, digits, or underscores, starting with a letter (it is trimmed and lowercased). `description`: optional, up to 255 characters. `PATCH` changes only the fields sent.

**Role**

```json
{ "id": "7c1e…", "name": "seller", "description": "Can sell. …", "is_system": true, "created_at": "2026-10-06T10:00:00Z" }
```

**Permission**

```json
{ "id": "a94b…", "code": "role.manage", "name": "Manage roles", "description": "Create, rename, …", "resource": "role", "action": "manage" }
```

## Errors

| Status | Message | When |
|---|---|---|
| 401 | `Authentication required` | No valid access token |
| 403 | `You do not have permission to perform this action` | The caller lacks the permission in the table above |
| 404 | `Role not found` / `Permission not found` / `Account not found` | Unknown id or code |
| 409 | `A role with this name already exists` | Create or rename |
| 422 | `System roles cannot be renamed or deleted` | `buyer`, `seller`, `admin` |
| 422 | `The admin role always holds every permission` | Adding to or removing from the `admin` role |
| 422 | `You cannot remove the admin role from your own account` | Self-demotion |
| 422 | field errors | Request validation |
