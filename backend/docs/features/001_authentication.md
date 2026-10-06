# 001 — Authentication

**Status:** `TESTING`. Code, migration, tests, and docs are written. The test suite has not been run yet (see [Progress](#progress)).

Business rules: [`README.md` §5.4](../../../README.md#54-authorization-and-ownership). API contract: [`docs/api/authentication.md`](../api/authentication.md). Tables: [`docs/database/database_schema.dbml`](../database/database_schema.dbml).

## Purpose

Prove who a person is, and keep that proof under their control: creating an account, verifying its email address, logging in, staying logged in across devices, logging out, and recovering or changing a password.

## Scope

| In this feature | Not in this feature |
|---|---|
| Accounts: registration, the caller's own account (`GET /auth/me`) | Editing the profile (name, phone, photo), deactivating an account → `002_users` |
| Email verification by one-time code | Phone verification (designed in the schema; no SMS provider chosen) |
| Login, access and refresh tokens, rotation, reuse detection | Roles, permissions, `require_permission`, the `buyer` role at registration, the first-admin bootstrap → `003_roles_and_permissions` |
| Session list, ending one session, logging out everywhere | Suspending an account (an admin action) → `015_admin` |
| Change password, forgot/reset password | Rate limiting (see [Known gaps](#known-gaps)) |

## Rules

**Accounts**

- One account per person, identified by email. Emails are stored and compared in lowercase.
- A phone number is optional at registration, in E.164 format, and unique.
- Passwords are 8 to 128 characters and stored only as an Argon2 hash.
- Only `active` accounts can log in or use an access token. `suspended` and `deactivated` accounts are locked out immediately, including with tokens issued earlier.

**Email verification (decided 2026-10-05: verify before login)**

- Registration emails a 6-digit code. **An account cannot log in until the code is confirmed.**
- A code is valid for 10 minutes, works once, and dies after 5 wrong guesses. A wrong guess is recorded even though the request fails.
- Asking for a new code invalidates the previous one.
- The request endpoint answers the same way whether or not the email belongs to an unverified account.

**Sessions**

- Login returns a JWT **access token** (15 minutes, not stored) and an opaque **refresh token** (30 days, stored only as a SHA-256 hash). Each login is one session, recorded with its user agent and IP address.
- A refresh token works **once**: refreshing revokes it and issues a new pair (rotation). The new refresh token gets a fresh 30 days, so a session stays alive for as long as it is used at least once every 30 days.
- **Reuse detection:** presenting a refresh token that was already rotated ends *every* session of the account, because a stale copy means the token leaked. A token that was merely logged out or revoked is just rejected.
- An access token stays valid until it expires, even after its session is ended. That is the trade-off of a stateless token, bounded by its 15-minute lifetime. Account status is checked on every request.

**Passwords**

- Changing the password requires the current one and ends every *other* session.
- "Forgot password" emails a single-use link valid for 30 minutes. Only the newest link works. Using it sets the new password and ends *every* session.
- The forgot-password endpoint answers the same way whether or not the email is registered.

**Error disclosure**

- A wrong password and an unknown email give the same `401`. "Email not verified" and "account not active" are only reported after the password has been checked.
- Verification and reset failures never say whether the account exists.

## Design

```
app/modules/auth/
├── auth_routes.py        # paths, schemas, status codes
├── auth_dependencies.py  # get_auth_service, get_current_account, get_current_auth
├── auth_service.py       # every rule above; owns the transaction
├── auth_repository.py    # queries only
├── auth_model.py         # Account, RefreshToken, VerificationCode, PasswordResetToken
├── auth_schema.py        # request/response contracts
├── auth_exceptions.py
└── auth_constants.py
```

Supporting pieces added with this feature:

| File | Role |
|---|---|
| `app/core/database.py` | Declarative base, mixins, engine, `get_session`. Sessions never auto-commit; the service commits. |
| `app/core/security.py` | Argon2 hashing, opaque tokens, OTP, JWT encode/decode. The only place PyJWT and pwdlib are imported. |
| `app/core/clock.py` | `utc_now()`; every timestamp is timezone-aware UTC. |
| `app/core/model_registry.py` | Imports every module's models for Alembic. |
| `app/infrastructure/notifications/email_sender.py` | `EmailSender` interface, SMTP adapter, and a logging stand-in for development. |
| `migrations/` + `alembic.ini` | Alembic (async). First migration creates the four tables. |

**For other modules:** protect an endpoint with `Depends(get_current_account)` from `auth_dependencies.py`. Reach accounts only through `AuthService`, never the repository (AGENTS.md §7).

**Transactions.** Each `AuthService` method is one unit of work and commits it. Two paths commit *before* raising on purpose: a wrong verification code (the attempt must be counted) and a reused refresh token (the sessions must be revoked). The verification code and the refresh/reset token rows are read `FOR UPDATE`, so concurrent requests are handled one at a time.

**Email.** Emails are sent after the commit. A delivery failure is logged and not raised: the code or link is already stored and can be requested again, and failing would reveal that the address has an account.

## Configuration

All in `app/config/settings.py`, documented in `.env.example`: `DATABASE_URL`, `JWT_SECRET_KEY` (required, ≥ 32 characters), `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`, `VERIFICATION_CODE_EXPIRE_MINUTES`, `VERIFICATION_CODE_MAX_ATTEMPTS`, `PASSWORD_RESET_TOKEN_EXPIRE_MINUTES`, `PASSWORD_RESET_URL`, and `SMTP_*`.

Without `SMTP_HOST`, emails are written to the log instead of sent. That is allowed in `development` and `test` only: `staging` and `production` refuse to start without SMTP.

## Security review

- [x] Passwords: Argon2, never logged or returned, length-capped to bound hashing cost.
- [x] Refresh tokens, reset tokens, and codes are stored as hashes only; raw values exist only in the response or the email.
- [x] No account enumeration through login, verification, or forgot-password responses.
- [x] Login runs a dummy hash for unknown emails, so response time doesn't reveal which emails exist.
- [x] Refresh tokens rotate; reuse is detected; password reset ends all sessions.
- [x] One-time codes are attempt-limited and compared in constant time.
- [x] Ownership: a session can only be listed or ended by its own account (`404` otherwise).
- [x] JWT: required claims (`exp`, `sub`, `sid`, `type`), fixed algorithm, secret length enforced.
- [x] Logs carry account ids only: no emails, passwords, tokens, or codes. (The development email stand-in logs the email body by design and cannot run in deployed environments.)

## Known gaps

These are not built. Each needs a decision or another feature first.

| Gap | Risk | Planned with |
|---|---|---|
| **No rate limiting** on login, verification-code requests, or forgot-password | Password guessing; email flooding of a known address | A rate-limiting piece (Redis is planned under `infrastructure/`). **Should be closed before launch.** |
| Emails are sent inside the request | A slow SMTP server slows the response, and response time can hint at whether an email is registered | `014_notifications` (background delivery) |
| Registration reports "email already exists" (`409`) | Reveals that an email is registered | Accepted for usability; revisit if required |
| The frontend can only tell "not verified" from "not active" by the message text | Fragile client logic | README §20 `I3` (machine-readable error codes) |
| `ip_address` is the direct peer's address | Behind a proxy it is the proxy's address unless the server is run with trusted proxy headers | Deployment docs |
| The `buyer` role is not assigned at registration | README says every account gets `buyer` | `003_roles_and_permissions`, whose migration must backfill existing accounts |
| Password-reset page URL (`PASSWORD_RESET_URL`) points at a frontend route that doesn't exist yet | The emailed link 404s until the page is built | Frontend |

## Progress

- [x] Requirements and rules (this document, README §5.4)
- [x] Database design and migration `0001`
- [x] Models, repository, service, schemas, routes, dependencies
- [x] Standard responses, error handling, logging
- [x] Tests written: `tests/api/auth/`, `tests/unit/core/test_security.py`, `tests/unit/config/test_settings.py`
- [x] API and feature documentation
- [ ] **Tests run and passing** (run by the user: `cd backend && .venv/Scripts/python -m pytest -q`)
- [x] Migration `0001` applied to the development database (2026-10-06)
- [ ] Rate limiting (see Known gaps)
