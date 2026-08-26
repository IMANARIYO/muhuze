# Authentication Database

## Conventions used throughout

- **Primary key**: UUID, via `UUIDPKMixin` (`app/core/database.py`) — not an auto-increment int.
- **Timestamps**: `created_at` / `updated_at`, via `TimestampMixin` — timezone-aware, server-side default (`now()`), `updated_at` auto-updates on write.
- **Table names**: snake_case, plural.
- Every table here is registered in `app/db/models.py` (the central Alembic model registry) and migrated via `alembic revision --autogenerate`.

---

## `accounts`

Table: `accounts` · Model: `app/modules/auth/models.py::Account`

The core authenticatable identity. Nothing else — no personal info, no
verification documents. See [README.md](README.md#does-not-handle).

| Column | Type | Nullable | Description |
|---|---|---:|---|
| id | UUID | No | Primary key |
| email | VARCHAR(255) | No | Unique, indexed. Login identifier. |
| phone | VARCHAR(20) | Yes | Unique, indexed. Not currently used for login — see [roadmap.md](roadmap.md) open question. |
| password_hash | VARCHAR(255) | No | Argon2 hash (`pwdlib`), never the raw password. |
| is_active | BOOLEAN | No | Default `true`. Login-disabled accounts (e.g. banned) would flip this to `false`. |
| is_verified | BOOLEAN | No | Default `false`. Set `true` by `POST /auth/email/verification/confirm`. See [note below](#a-note-on-is_verified). |
| created_at | TIMESTAMPTZ | No | |
| updated_at | TIMESTAMPTZ | No | |

### A note on `is_verified`

`Account.is_verified` means **"this account confirmed its own email"** — set
the moment `POST /auth/email/verification/confirm` succeeds. It has **no
relationship** to seller eligibility.

Seller verification (documents, admin approve/reject, gates withdrawals) is a
completely separate concept, tracked on `seller_verification.status` in the
`seller_verification` module — not built yet. Do not read one as implying the
other:

```
Account.is_verified = true         # this person confirmed their email
SellerVerification.status = pending # ...says nothing about whether they can sell/withdraw
```

---

## `refresh_tokens`

Table: `refresh_tokens` · Model: `app/modules/auth/models.py::RefreshToken`

Lets a client exchange a still-valid refresh token for a new access token
without re-entering credentials. Only a hash is ever stored — the raw token
is returned to the client once, at issuance, and never persisted.

| Column | Type | Nullable | Description |
|---|---|---:|---|
| id | UUID | No | Primary key |
| account_id | UUID | No | FK → `accounts.id`, indexed |
| token_hash | VARCHAR(64) | No | SHA-256 hex digest of the raw token. Unique, indexed — looked up by exact match. Fast hash, not Argon2: the raw token is already high-entropy (`secrets.token_urlsafe(64)`), unlike a password. |
| expires_at | TIMESTAMPTZ | No | `now() + REFRESH_TOKEN_EXPIRE_DAYS` (default 30) at issuance |
| revoked_at | TIMESTAMPTZ | Yes | Set on logout, on rotation, or in bulk on password reset (see below) |
| created_at | TIMESTAMPTZ | No | |
| updated_at | TIMESTAMPTZ | No | |

### Rotation

`POST /auth/refresh` always **revokes the token it was given** and issues a
brand-new refresh token alongside the new access token. A refresh token is
therefore single-use. This means a stolen-and-replayed refresh token is
detectable: the legitimate client's next refresh attempt will find its token
already revoked.

### Bulk revocation on password reset

`PasswordResetService.reset_password` calls
`RefreshTokenRepository.revoke_all_for_account` — every session is
invalidated the moment a password is reset, since anything issued under the
old password can no longer be trusted.

---

## `verification_codes`

Table: `verification_codes` · Model: `app/modules/auth/models.py::VerificationCode`

A one-time code proving control of an email (or, eventually, a phone number
— the `purpose` column already supports it, only the email flow is wired up
today). Only the hash is stored.

| Column | Type | Nullable | Description |
|---|---|---:|---|
| id | UUID | No | Primary key |
| account_id | UUID | No | FK → `accounts.id`, indexed |
| purpose | VARCHAR(30) | No | `email_verification` \| `phone_verification` (`VerificationPurpose` enum in code). Only `email_verification` has an endpoint. |
| code_hash | VARCHAR(64) | No | SHA-256 of the 6-digit OTP |
| expires_at | TIMESTAMPTZ | No | `now() + OTP_EXPIRE_MINUTES` (default 10) |
| verified_at | TIMESTAMPTZ | Yes | Set on successful confirm |
| created_at | TIMESTAMPTZ | No | |
| updated_at | TIMESTAMPTZ | No | |

Multiple valid codes for the same account+purpose can coexist (e.g.
requesting a resend doesn't invalidate the previous one) — confirming with
any one of them succeeds. A code can't be reused once `verified_at` is set.

---

## `password_reset_tokens`

Table: `password_reset_tokens` · Model: `app/modules/auth/models.py::PasswordResetToken`

Forgot-password flow. Deliberately not columns on `Account` — a user can
request multiple resets, tokens expire and are one-time use.

| Column | Type | Nullable | Description |
|---|---|---:|---|
| id | UUID | No | Primary key |
| account_id | UUID | No | FK → `accounts.id`, indexed |
| token_hash | VARCHAR(64) | No | SHA-256 of the raw token. Unique, indexed. |
| expires_at | TIMESTAMPTZ | No | `now() + PASSWORD_RESET_TOKEN_EXPIRE_MINUTES` (default 30) |
| used_at | TIMESTAMPTZ | Yes | Set once consumed — enforces single-use |
| created_at | TIMESTAMPTZ | No | |
| updated_at | TIMESTAMPTZ | No | |

`POST /auth/password/forgot` always returns success whether or not the email
is registered — an error response would itself leak which emails exist in
the system.

---

## `roles`, `permissions`, `account_roles`, `role_permissions`, `account_permissions`

Models: `app/modules/auth/models.py::{Role, Permission, AccountRole, RolePermission, AccountPermission}`

Standard RBAC shape, plus one deliberate extra: an account can hold a
permission two ways — through a role, or granted directly. `AccountRole`,
`RolePermission`, and `AccountPermission` are all many-to-many join tables,
each with a `UniqueConstraint` preventing the same pair being granted twice.

| Table | Columns beyond id/timestamps | Notes |
|---|---|---|
| `roles` | `name` (unique, indexed), `description` | Seeded by the migration that created this table: **`buyer`, `seller`, `admin`**. Dynamic — an admin can grant/revoke these on accounts via the API; creating *new* roles isn't built (see [roadmap.md](roadmap.md)). |
| `permissions` | `code` (unique, indexed), `name`, `description`, `resource` (indexed), `action` | **Empty catalog today** — code-defined, database-synced. See [permissions-sync.md](permissions-sync.md) for the full design; don't populate this by hand. |
| `account_roles` | `account_id` (FK), `role_id` (FK) | Unique on `(account_id, role_id)` |
| `role_permissions` | `role_id` (FK), `permission_id` (FK, `ondelete="CASCADE"`) | Unique on `(role_id, permission_id)`. The cascade means deleting a stale permission automatically cleans up its role assignments — see [permissions-sync.md](permissions-sync.md#why-deletion-is-safe-cascade-not-a-two-step-dance). |
| `account_permissions` | `account_id` (FK), `permission_id` (FK, `ondelete="CASCADE"`) | Unique on `(account_id, permission_id)`. A permission granted straight to one account, bypassing roles — same cascade reasoning as `role_permissions`. |

**Every account gets the `buyer` role automatically at registration**
(`AuthService.register`). No other role is assigned automatically today —
`seller` and `admin` are granted via the role-management endpoints (see
[README.md](README.md#endpoints)); `admin` also has the startup-bootstrap
path (see [bootstrap.md](bootstrap.md)) for creating the very first one.

**Permissions are not admin-creatable, unlike roles.** A permission that
doesn't correspond to a real check in the code is meaningless. See
[permissions-sync.md](permissions-sync.md).

### Effective permissions: role-based ∪ direct

`AuthorizationRepository.get_permission_codes` — what `has_permission` /
`require_permission` / `/me/authorization` all actually use — is the
**union** of an account's role-derived permissions and its direct grants,
deduplicated:

```
effective_permissions(account) =
    permissions from account's roles (via role_permissions)
    ∪
    permissions granted directly to the account (via account_permissions)
```

Concretely: a `seller` role might grant `products.create`, `products.read`,
`products.update`. If this particular seller also needs
`products.publish` without changing what *every* seller can do, grant it
directly — `POST /auth/accounts/{id}/permissions`. It shows up in their
effective permissions immediately, and if their `seller` role is later
revoked, the direct grant is untouched (the two are fully independent —
removing a role never removes a direct permission, and vice versa; verified
in `tests/test_direct_permissions.py::test_direct_permission_survives_role_removal`).

**GRANT only — no DENY.** There's no way for a direct permission (or
anything else) to *revoke* a permission a role would otherwise grant.
Introducing role-grants-but-account-denies precedence is a real design
problem worth avoiding until there's a concrete need for it; union-only
is simple and predictable.

### Using this from another module

Don't query these tables directly — use the dependency factories in
`auth/dependencies.py`:

```python
Depends(require_role("admin"))
Depends(require_permission("products.delete"))
```

See [README.md](README.md#for-other-modules-gating-an-endpoint-by-rolepermission)
and, for how a module actually gets its permissions into the database in
the first place, [permissions-sync.md](permissions-sync.md).

---

## Relationships

```
accounts (1) ──── (0..N) refresh_tokens
accounts (1) ──── (0..N) verification_codes
accounts (1) ──── (0..N) password_reset_tokens
accounts (M) ──── (N) roles           via account_roles
roles    (M) ──── (N) permissions     via role_permissions
accounts (M) ──── (N) permissions     via account_permissions (direct grants)
```
