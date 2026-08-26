from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import Permission
from app.shared.permissions import PermissionDefinition


@dataclass
class SyncResult:
    inserted: list[str]
    updated: list[str]
    removed: list[str]
    unchanged: list[str]


async def sync_permissions(
    db: AsyncSession,
    definitions: list[PermissionDefinition],
    *,
    remove_stale: bool = False,
) -> SyncResult:
    """Reconciles the given permission definitions into the database: code
    is the source of truth.

    - Missing definitions are inserted.
    - Existing permissions whose metadata (name/description/resource/action)
      no longer matches the definition are updated in place — the code is
      the identity, everything else can drift and gets corrected.
    - Permissions that exist in the database but no longer appear in
      `definitions` are left alone unless `remove_stale=True`, in which case
      they're deleted (their role_permissions rows cascade-delete with them
      — see RolePermission.permission_id's `ondelete="CASCADE"`).

    Does not commit; the caller controls the transaction.
    """
    result = await db.execute(select(Permission))
    existing = {permission.code: permission for permission in result.scalars().all()}
    defined_by_code = {definition.code: definition for definition in definitions}

    inserted: list[str] = []
    updated: list[str] = []
    unchanged: list[str] = []

    for code, definition in defined_by_code.items():
        current = existing.get(code)
        if current is None:
            db.add(
                Permission(
                    code=definition.code,
                    name=definition.name,
                    description=definition.description,
                    resource=definition.resource,
                    action=definition.action,
                )
            )
            inserted.append(code)
            continue

        changed = (
            current.name != definition.name
            or current.description != definition.description
            or current.resource != definition.resource
            or current.action != definition.action
        )
        if changed:
            current.name = definition.name
            current.description = definition.description
            current.resource = definition.resource
            current.action = definition.action
            updated.append(code)
        else:
            unchanged.append(code)

    removed: list[str] = []
    if remove_stale:
        for code in set(existing) - set(defined_by_code):
            await db.delete(existing[code])
            removed.append(code)

    await db.flush()
    return SyncResult(
        inserted=sorted(inserted),
        updated=sorted(updated),
        removed=sorted(removed),
        unchanged=sorted(unchanged),
    )
