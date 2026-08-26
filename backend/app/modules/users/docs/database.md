# Users Database

Conventions (UUID PK, timestamp mixin, table naming) are shared across all
modules — see [`auth/docs/database.md`](../../auth/docs/database.md#conventions-used-throughout).

## `profiles`

Table: `profiles` · Model: `app/modules/users/models.py::Profile`

| Column | Type | Nullable | Description |
|---|---|---:|---|
| id | UUID | No | Primary key |
| account_id | UUID | No | FK → `accounts.id`. **Unique** — enforces the 1:1 with `Account` at the DB level, not just in application code. |
| first_name | VARCHAR(100) | No | |
| last_name | VARCHAR(100) | No | |
| date_of_birth | DATE | Yes | |
| created_at | TIMESTAMPTZ | No | |
| updated_at | TIMESTAMPTZ | No | |

### Why upsert instead of separate create/update endpoints

`Account` and `Profile` are created at different times (register, then fill
in your profile later) but from the client's point of view "save my
profile" is one action regardless of whether a row exists yet. `PUT
/users/me` creates the row if missing, updates it if present — the client
never needs to know which case it is.

## Relationships

```
accounts (1) ──── (0..1) profiles
```

Unlike `refresh_tokens` (one account, many rows), a `Profile` is capped at
one per account by the unique constraint on `account_id`.
