# Startup Account Bootstrap

## The problem this solves

Role management is gated by `require_role("admin")` — but nothing can grant
the `admin` role without an existing admin to grant it. Something has to
create the first one outside the normal register → assign-role path.

## The mechanism

`app/core/bootstrap.py::seed_default_accounts(db)` runs once per process,
from `app/main.py`'s `lifespan` — every time the app starts, not on a
schedule and not via a manual command. It's idempotent: each seeded account
is looked up by email first, and skipped if it already exists. Re-running
it (which happens on every restart) never duplicates an account, never
touches its password, and never re-grants a role it already has.

Two accounts, both entirely optional and both driven by env vars — unset
means "don't seed this one," not an error:

| Env vars | Role(s) granted | Environment restriction |
|---|---|---|
| `SUPER_ADMIN_EMAIL`, `SUPER_ADMIN_PASSWORD` | `admin` | None — an admin must be reachable in every environment, including production |
| `TEST_SELLER_EMAIL`, `TEST_SELLER_PASSWORD` | `buyer`, `seller` | **Skipped outright when `ENVIRONMENT=production`**, even if the vars are set — this account exists for local/staging testing convenience, not for real deployments |

Both seeded accounts are created with `is_verified=True` — they're
system-provisioned, not registered through the normal email-verification
flow.

## Why env vars, not a migration seed

Roles (`buyer`/`seller`/`admin`) are seeded via migration because they're
the same everywhere — they're structural. *Which account* holds the admin
role is environment-specific and sensitive (a password), which is exactly
what `.env` / real secret managers are for, not source-controlled migration
data. `.env` itself is gitignored — see `backend/.gitignore`.

## Local dev values

The `.env` in this repo has working dev-only credentials for both
accounts, so `admin@muhuze.com` / `seller@muhuze.com` are usable
immediately after a fresh clone + `alembic upgrade head` + starting the
app. **Rotate both before any shared or production deployment** — the
values currently in `.env` are not secret-worthy beyond a single
developer's machine.

## What's still manual

There's no way yet to grant `admin` or `seller` to an *arbitrary* account
(only these two fixed, env-configured ones exist). Broader role management
(admin grants roles to any account, creates new roles, etc.) needs the
`admin` module — the super-admin seeded here is exactly what makes
building that module's first `require_role("admin")` endpoint possible.
