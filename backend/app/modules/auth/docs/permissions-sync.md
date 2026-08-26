# Permission Registry & Sync

## The rule

**The codebase is the source of truth for which permissions exist. The
database is the runtime store of those permissions.** Roles are dynamic —
an admin can create a role and assign it any combination of existing
permissions. Permissions are not: nobody invents a permission through an
API or admin UI, because a permission that doesn't correspond to a real
authorization check in the code is meaningless (and dangerous — it would
look like it does something).

```
Module's permissions.py  →  app/db/permissions.py  →  sync script  →  permissions table
     (code, static)          (aggregates all)         (reconciles)      (runtime store)
                                                              │
                                                              ▼
                                                        role_permissions
                                                              │
                                                              ▼
                                                            roles
                                                       (admin-manageable)
```

## Why permissions aren't just role names

Hard-coding `if account.role == "admin"` scattered across the codebase
means every new role requires a code change everywhere that checks it, and
"can Finance approve withdrawals but not delete products" isn't
expressible. Instead: permissions describe capabilities
(`withdrawals.approve`), roles are named bundles of them, and an account's
authorization comes from its roles. See `auth/docs/database.md`'s
`roles`/`permissions`/`account_roles`/`role_permissions` section for the
schema.

**Permissions are resource + action, not necessarily CRUD.** `orders.cancel`
and `withdrawals.approve` are business actions, not database operations —
don't force every permission into create/read/update/delete.

## How a module adds permissions

1. Add `app/modules/<module>/permissions.py`:

   ```python
   from app.shared.permissions import PermissionDefinition

   PRODUCT_PERMISSIONS = [
       PermissionDefinition(
           code="products.delete",
           name="Delete products",
           resource="products",
           action="delete",
           description="Allows deleting any product, not just your own",
       ),
       ...,
   ]
   ```

2. Add one import to `app/db/permissions.py` (the same pattern as
   `app/db/models.py` for ORM models):

   ```python
   from app.modules.products.permissions import PRODUCT_PERMISSIONS

   ALL_PERMISSIONS = [
       *PRODUCT_PERMISSIONS,
   ]
   ```

3. Run the sync (see below) so the definitions actually reach the database.

4. Gate the endpoint:

   ```python
   Depends(require_permission("products.delete"))
   ```

**Don't invent permissions for a module that doesn't exist yet.** As of
this writing `ALL_PERMISSIONS` is empty — no module has an authorization
need finer than a role check. That's the correct state, not a gap to fill
speculatively.

## The sync script

`app/core/permissions_sync.py::sync_permissions(db, definitions, *,
remove_stale=False)` reconciles `definitions` (normally
`app/db/permissions.py::ALL_PERMISSIONS`) into the `permissions` table:

- **Missing** (in code, not in DB) → inserted.
- **Existing and matching** → left alone.
- **Existing but metadata changed** (name/description/resource/action) →
  updated in place. Code is authoritative for these fields too, not just
  existence.
- **In DB but no longer in code** → left alone, *unless* `remove_stale=True`,
  in which case deleted.

Run it via `app/scripts/sync_permissions.py`:

```
python -m app.scripts.sync_permissions               # add + update only
python -m app.scripts.sync_permissions --remove-stale # also delete stale ones
```

This is a deliberate, run-by-hand-or-in-deploy step — **not** something
that runs automatically on every app startup. A stale permission
disappearing because someone typo'd a code and redeployed should never
happen silently on a financial system like MUHUZE.

### Why deletion is safe: cascade, not a two-step dance

`RolePermission.permission_id` has `ondelete="CASCADE"`. Deleting a
permission automatically deletes every `role_permissions` row that
referenced it — enforced by Postgres itself, not by application code
remembering to clean up first. Two layers of safety: the sync script only
deletes what `remove_stale=True` explicitly opts into, and the database
guarantees referential integrity regardless of what the application does.

## Current state

- `ALL_PERMISSIONS` is empty. No real permission has been defined by any
  module yet.
- The mechanism itself is tested in `tests/test_permissions_sync.py`
  (insert, idempotency, metadata update, stale-left-alone,
  stale-removed, cascade-to-role_permissions) using throwaway test
  definitions — not by inventing production permissions just to exercise
  the code path.
- `require_permission(*codes)` (in `auth/dependencies.py`) is ready to use
  the moment a module defines its first real permission.
