# Authentication Module

## Purpose

Manages account identity and everything about proving/controlling it:
registration, login, token issuance/rotation, email verification, password
recovery, and authorization (roles/permissions).

## Responsibilities

- **Accounts** — registration, login (`accounts`)
- **Sessions** — access/refresh token issuance, rotation, revocation (`refresh_tokens`)
- **Email verification** — one-time codes (`verification_codes`)
- **Password recovery** — forgot/reset flow (`password_reset_tokens`)
- **Authorization** — roles and permissions, and who holds which (`roles`, `permissions`, `account_roles`, `role_permissions`)

## Does Not Handle

- **Personal information** (first name, last name, DOB, address) — that's `users` (`Profile`, 1:1 with `Account`).
- **Seller identity verification** (documents, admin approve/reject) — that's `seller_verification`. Not to be confused with `Account.is_verified` — see [database.md](database.md#a-note-on-is_verified).
- Orders, payments, wallets, referrals, or anything financial.

## Architecture

Each endpoint flows through 4 layers:

```
router.py       → route declarations only (path, method, request/response schema)
controller.py    → HTTP layer: translates schemas ⇄ service calls
service.py       → business rules (password hashing, token rotation, eligibility checks)
repository.py    → data access only (SQLAlchemy queries), no business rules
```

`service.py` and `repository.py` each hold multiple classes, one per concern
(`AuthService`/`AccountRepository`, `VerificationService`/`VerificationCodeRepository`,
`PasswordResetService`/`PasswordResetTokenRepository`,
`AuthorizationService`/`AuthorizationRepository`) — one `AuthController` wires
them all together, since together they *are* the auth module's HTTP surface.

**Email delivery is stubbed.** `app/core/notifications.py::send_email` logs
instead of actually sending — there's no email/SMS provider configured yet.
Every OTP/reset-token flow is otherwise complete; swapping in a real
provider (SES/SendGrid/etc.) means changing that one function, not the
domain logic. See [roadmap.md](roadmap.md).

## Endpoints

| Method | Path | Auth required | Purpose |
|---|---|---|---|
| POST | `/api/v1/auth/register` | No | Create an `Account` (auto-assigned the `buyer` role) |
| POST | `/api/v1/auth/login` | No | Verify credentials, issue access + refresh token |
| POST | `/api/v1/auth/refresh` | No (refresh token in body) | Exchange a valid refresh token for a new pair (rotates the old one) |
| POST | `/api/v1/auth/logout` | No (refresh token in body) | Revoke a refresh token |
| POST | `/api/v1/auth/email/verification/request` | Yes | Send an OTP to the caller's own email |
| POST | `/api/v1/auth/email/verification/confirm` | Yes | Confirm the OTP, sets `Account.is_verified = true` |
| POST | `/api/v1/auth/password/forgot` | No | Request a reset token by email (always 200 — doesn't reveal whether the email exists) |
| POST | `/api/v1/auth/password/reset` | No (reset token in body) | Consume the token, set a new password, revoke all refresh tokens |
| GET | `/api/v1/auth/me/authorization` | Yes | The caller's own roles + permissions |
| GET | `/api/v1/auth/roles` | Admin | List all roles |
| GET | `/api/v1/auth/permissions` | Admin | List all permissions (the synced catalog — see [permissions-sync.md](permissions-sync.md)) |
| POST | `/api/v1/auth/accounts/{account_id}/roles` | Admin | Grant an existing role to an account (body: `{"role_name": "..."}`) |
| DELETE | `/api/v1/auth/accounts/{account_id}/roles/{role_name}` | Admin | Revoke a role from an account |
| POST | `/api/v1/auth/roles/{role_name}/permissions` | Admin | Grant an existing permission to a role (body: `{"permission_code": "..."}`) |
| DELETE | `/api/v1/auth/roles/{role_name}/permissions/{permission_code}` | Admin | Revoke a permission from a role |

None of these *create* roles or permissions — roles are seeded (`buyer`/`seller`/`admin`, see `database.md`) and permissions are code-synced (see [permissions-sync.md](permissions-sync.md)). These endpoints only manage assignment: which account has which role, which role has which permission. "Admin" means [`require_role("admin")`](#for-other-modules-gating-an-endpoint-by-rolepermission) — see [bootstrap.md](bootstrap.md) for how the first admin account comes to exist.

## For other modules: gating an endpoint by role/permission

`auth/dependencies.py` exports two dependency factories any module can use:

```python
from app.modules.auth.dependencies import require_role, require_permission

@router.delete("/{product_id}")
async def delete_product(
    account: Account = Depends(require_role("admin", "seller")),
    ...
```

Both resolve the caller via `get_current_account` first (so an unauthenticated
request gets `401`, not `403`) and raise `InsufficientPermissionsError` (403)
if the caller lacks every named role/permission.

See [database.md](database.md) for table schemas and [roadmap.md](roadmap.md) for what's done vs. planned.
