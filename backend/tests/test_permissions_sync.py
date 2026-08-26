import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions_sync import sync_permissions
from app.modules.auth.models import Permission, Role, RolePermission
from app.shared.permissions import PermissionDefinition


def unique_code() -> str:
    return f"test.{uuid.uuid4().hex}"


def definition(
    code: str, *, name: str = "Test permission", resource: str = "test"
) -> PermissionDefinition:
    return PermissionDefinition(
        code=code,
        name=name,
        resource=resource,
        action="read",
        description="A test permission",
    )


async def get_permission(db: AsyncSession, code: str) -> Permission | None:
    result = await db.execute(select(Permission).where(Permission.code == code))
    return result.scalar_one_or_none()


async def cleanup(db: AsyncSession, *codes: str) -> None:
    """remove_stale sweeps the whole table, so any code a test creates and
    doesn't itself remove must be cleaned up — otherwise it leaks into a
    later test's remove_stale sweep on this shared dev DB."""
    for code in codes:
        permission = await get_permission(db, code)
        if permission is not None:
            await db.delete(permission)
    await db.commit()


async def test_sync_inserts_missing_permission(db: AsyncSession) -> None:
    code = unique_code()
    result = await sync_permissions(db, [definition(code)])
    await db.commit()
    try:
        assert result.inserted == [code]
        assert result.updated == []
        assert result.unchanged == []
        assert await get_permission(db, code) is not None
    finally:
        await cleanup(db, code)


async def test_sync_is_idempotent(db: AsyncSession) -> None:
    code = unique_code()
    await sync_permissions(db, [definition(code)])
    await db.commit()
    try:
        result = await sync_permissions(db, [definition(code)])
        await db.commit()

        assert result.inserted == []
        assert result.updated == []
        assert result.unchanged == [code]
    finally:
        await cleanup(db, code)


async def test_sync_updates_changed_metadata(db: AsyncSession) -> None:
    code = unique_code()
    await sync_permissions(db, [definition(code, name="Old name")])
    await db.commit()
    try:
        result = await sync_permissions(db, [definition(code, name="New name")])
        await db.commit()

        assert result.updated == [code]
        permission = await get_permission(db, code)
        assert permission is not None
        assert permission.name == "New name"
    finally:
        await cleanup(db, code)


async def test_sync_without_remove_stale_leaves_extra_permissions(
    db: AsyncSession,
) -> None:
    keep_code = unique_code()
    stale_code = unique_code()
    await sync_permissions(db, [definition(keep_code), definition(stale_code)])
    await db.commit()
    try:
        result = await sync_permissions(db, [definition(keep_code)])
        await db.commit()

        assert result.removed == []
        assert await get_permission(db, stale_code) is not None
    finally:
        await cleanup(db, keep_code, stale_code)


async def test_sync_with_remove_stale_deletes_extra_permissions(
    db: AsyncSession,
) -> None:
    keep_code = unique_code()
    stale_code = unique_code()
    await sync_permissions(db, [definition(keep_code), definition(stale_code)])
    await db.commit()
    try:
        result = await sync_permissions(db, [definition(keep_code)], remove_stale=True)
        await db.commit()

        assert stale_code in result.removed
        assert keep_code not in result.removed
        assert await get_permission(db, keep_code) is not None
        assert await get_permission(db, stale_code) is None
    finally:
        await cleanup(db, keep_code, stale_code)


async def test_remove_stale_cascades_role_assignment_deletion(db: AsyncSession) -> None:
    keep_code = unique_code()
    stale_code = unique_code()
    await sync_permissions(db, [definition(keep_code), definition(stale_code)])
    await db.commit()
    stale_permission = await get_permission(db, stale_code)
    assert stale_permission is not None

    role = Role(name=f"test-role-{uuid.uuid4().hex}")
    db.add(role)
    await db.flush()
    db.add(RolePermission(role_id=role.id, permission_id=stale_permission.id))
    await db.commit()
    try:
        await sync_permissions(db, [definition(keep_code)], remove_stale=True)
        await db.commit()

        result = await db.execute(
            select(RolePermission).where(
                RolePermission.permission_id == stale_permission.id
            )
        )
        assert result.scalar_one_or_none() is None
    finally:
        await cleanup(db, keep_code, stale_code)
        await db.delete(role)
        await db.commit()
