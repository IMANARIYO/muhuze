# Users Module

## Purpose

Owns the authenticated account's personal information — the `Profile`,
1:1 with `Account`. Kept separate from `auth` on purpose: `auth` proves
*who you are*, `users` describes *who that is*. See
[`auth/docs/README.md`](../../auth/docs/README.md#does-not-handle).

## Responsibilities

- Fetching the caller's own profile.
- Creating/updating the caller's own profile (upsert — see [database.md](database.md)).

## Does Not Handle

- **Authentication** (login, tokens, password) — `auth`.
- **Seller-specific data** (business info, identity documents) — `sellers` / `seller_verification`, not built yet.
- Any other account's profile. There is currently no "view another user's public profile" endpoint, and no admin listing — every endpoint here operates on the caller's own account, resolved via `get_current_account` (from `auth`).

## Architecture

Same 4-layer convention as every module (`router.py → controller.py → service.py → repository.py`).

`GET /me` and `PUT /me` both depend on `app.modules.auth.dependencies.get_current_account` to resolve *whose* profile is being read/written — there is no `account_id` path parameter, by design (prevents one account from reading/writing another's profile by guessing an ID).

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/users/me` | Fetch the caller's profile. `404` if they haven't created one yet. |
| PUT | `/api/v1/users/me` | Create-or-update (upsert) the caller's profile. |

Requires `Authorization: Bearer <access_token>` on both.

See [database.md](database.md) for the table schema and [roadmap.md](roadmap.md) for what's planned next.
