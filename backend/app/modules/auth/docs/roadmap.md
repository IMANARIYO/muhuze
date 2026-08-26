# Authentication Roadmap

## Phase 1 — Account

- [x] `Account` model + migration
- [x] `AccountRepository` (`get_by_email`, `get_by_id`, `create`, `mark_verified`, `update_password`)
- [x] Registration service (`AuthService.register` — rejects duplicate email, assigns default `buyer` role)
- [x] `POST /api/v1/auth/register`

## Phase 2 — Login & sessions

- [x] Password verification (Argon2 via `pwdlib`)
- [x] JWT access token (`core/security.py::create_access_token`)
- [x] `RefreshToken` model + migration
- [x] `RefreshTokenRepository` (`create`, `get_by_token_hash`, `revoke`, `revoke_all_for_account`)
- [x] `POST /api/v1/auth/login` — returns access + refresh token
- [x] `POST /api/v1/auth/refresh` — validates, rotates (old token revoked, new pair issued)
- [x] `POST /api/v1/auth/logout` — revokes a refresh token, idempotent on unknown tokens
- [x] `get_current_account` dependency — JWT-gates any endpoint in any module

## Phase 3 — Verification

- [x] `VerificationCode` model + migration (`purpose` column supports email and phone; only email is wired up)
- [x] `VerificationCodeRepository` (`create`, `get_valid`, `mark_verified`)
- [x] Email verification (`POST /auth/email/verification/request`, `POST /auth/email/verification/confirm`, sets `Account.is_verified`)
- [x] OTP expiration (`OTP_EXPIRE_MINUTES`, default 10)
- [x] "Resend" — just call `/request` again; old unverified codes stay valid until they expire, no explicit invalidation needed
- [ ] Phone verification — same table, same code path, just needs an SMS sender + endpoint when there's an SMS provider
- [ ] Real email delivery — currently `app/core/notifications.py::send_email` logs instead of sending (no provider configured)

## Phase 4 — Password recovery

- [x] `PasswordResetToken` model + migration
- [x] `PasswordResetTokenRepository` (`create`, `get_valid_by_token_hash`, `mark_used`)
- [x] `POST /auth/password/forgot` — always 200, doesn't reveal whether the email exists
- [x] `POST /auth/password/reset` — consumes token (single-use), sets new password, revokes all refresh tokens
- [ ] Real email delivery — same gap as Phase 3

## Phase 5 — Authorization (roles & permissions)

- [x] `Role`, `Permission`, `AccountRole`, `RolePermission`, `AccountPermission` models + migration
- [x] Default roles seeded in the migration: `buyer`, `seller`, `admin`
- [x] `AuthorizationRepository` (role/permission lookups and assignment)
- [x] Every account auto-assigned `buyer` at registration
- [x] `GET /auth/me/authorization` — caller's own roles + permissions, combined
- [x] `GET /auth/me/roles` / `GET /auth/me/permissions` — split out separately, fetched on demand after login rather than bundled into the login response (deliberate: keeps login lean, a client asks only when it actually needs authorization data)
- [x] `require_role(*names)` / `require_permission(*codes)` dependency factories, usable by any module
- [x] Permission metadata (`name`, `resource`, `action`) columns + `role_permissions.permission_id` `ondelete="CASCADE"`
- [x] `PermissionDefinition` (`app/shared/permissions.py`) + central registry (`app/db/permissions.py`) + sync engine (`app/core/permissions_sync.py`) + CLI (`python -m app.scripts.sync_permissions [--remove-stale]`) — full design in [permissions-sync.md](permissions-sync.md)
- [x] Startup bootstrap (`app/core/bootstrap.py`, wired into `main.py`'s `lifespan`): seeds one `admin` account and one `buyer`+`seller` test account from env vars (`SUPER_ADMIN_EMAIL`/`SUPER_ADMIN_PASSWORD`, `TEST_SELLER_EMAIL`/`TEST_SELLER_PASSWORD`), idempotent, test-seller skipped in production — see [bootstrap.md](bootstrap.md). Solves the "how does the first admin exist" bootstrap problem.
- [x] Role/permission management endpoints, all `require_role("admin")`-gated: `GET /roles`, `GET /permissions`, `POST/DELETE/GET /accounts/{id}/roles[/{role_name}]`, `POST/DELETE/GET /roles/{role_name}/permissions[/{code}]` — any admin can grant any *existing* role to any account and any *existing* permission to any role, and inspect either relationship for one specific account/role (not just the global lists). Doesn't create roles or permissions (see [permissions-sync.md](permissions-sync.md) for why permissions specifically never get an API), only manages assignment.
- [x] `require_permission` proven end-to-end despite the empty catalog: `test_role_management.py`'s `test_require_permission_dependency_denies_then_grants_after_assignment` syncs a throwaway permission, assigns it role→account through the real endpoints, and calls the dependency directly — denies before assignment, grants after
- [x] Direct account permissions (`AccountPermission`) — a permission granted straight to one account, bypassing roles entirely. Effective permissions (what `has_permission`/`require_permission`/`/me/authorization` all use) = role-derived ∪ direct, deduplicated. `POST/DELETE /auth/accounts/{id}/permissions[/{code}]` + `GET` to list an account's direct grants. GRANT only — no DENY/override semantics, deliberately (see [database.md](database.md#effective-permissions-role-based--direct)). Verified: survives role removal, dedupes when granted both ways, and `require_permission` grants access via a direct grant with zero roles involved (`tests/test_direct_permissions.py`)
- [ ] `sellers` module itself is still paused mid-build — separate from role assignment
- [ ] Permission catalog is empty — no endpoint anywhere calls `require_permission` yet; the sync mechanism and the assignment chain are both proven (tested in isolation), just waiting for the first module with a real gating need. Don't invent codes speculatively.
- [ ] Creating new roles (beyond the seeded `buyer`/`seller`/`admin`) — not built; wasn't asked for yet and the 3 seeded roles cover everything built so far

## Open questions

- **Login identifier**: `email` and `phone` are both unique+indexed, but only
  `email` is required and only `email` is used for login today. Decide
  whether `phone` becomes an alternate login identifier or stays
  contact-only metadata.
- **"Log out everywhere"**: partially covered — password reset now revokes
  every refresh token, but there's no user-facing "log out of all devices"
  action independent of a password change. Would reuse
  `revoke_all_for_account`.
- **Multiple roles per account**: the schema already supports it
  (`account_roles` is many-to-many) — a seller who is also a buyer just gets
  two rows. Nothing to design further here; this was resolved by the RBAC
  shape itself.
