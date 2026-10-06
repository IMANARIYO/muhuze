"""Data access for roles and permissions. No business rules, and no commits:
the service owns the transaction (AGENTS.md §13)."""

import uuid

from sqlalchemy import Select, delete, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.authorization.authorization_model import (
    AccountPermission,
    AccountRole,
    Permission,
    Role,
    RolePermission,
)
from app.shared.responses.pagination import PaginationParams


class AuthorizationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Roles ────────────────────────────────────────────────────────────

    async def get_role(self, role_id: uuid.UUID) -> Role | None:
        return await self._session.get(Role, role_id)

    async def get_role_by_name(self, name: str) -> Role | None:
        return await self._session.scalar(select(Role).where(Role.name == name))

    async def list_roles(self, pagination: PaginationParams) -> tuple[list[Role], int]:
        return await self._paginate(select(Role).order_by(Role.name), pagination)

    async def add_role(self, role: Role) -> None:
        self._session.add(role)
        await self._session.flush()

    async def delete_role(self, role: Role) -> None:
        await self._session.delete(role)
        await self._session.flush()

    # ── Permissions ──────────────────────────────────────────────────────

    async def get_permission_by_code(self, code: str) -> Permission | None:
        return await self._session.scalar(select(Permission).where(Permission.code == code))

    async def get_all_permissions(self) -> list[Permission]:
        return list(await self._session.scalars(select(Permission)))

    async def list_permissions(
        self, pagination: PaginationParams, *, resource: str | None
    ) -> tuple[list[Permission], int]:
        statement = select(Permission).order_by(Permission.code)
        if resource is not None:
            statement = statement.where(Permission.resource == resource)
        return await self._paginate(statement, pagination)

    async def add_permission(self, permission: Permission) -> None:
        self._session.add(permission)
        await self._session.flush()

    async def delete_permission(self, permission: Permission) -> None:
        await self._session.delete(permission)
        await self._session.flush()

    # ── Role ↔ permission ────────────────────────────────────────────────

    async def list_role_permissions(
        self, role_id: uuid.UUID, pagination: PaginationParams
    ) -> tuple[list[Permission], int]:
        statement = (
            select(Permission)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == role_id)
            .order_by(Permission.code)
        )
        return await self._paginate(statement, pagination)

    async def add_permission_to_role(self, *, role_id: uuid.UUID, permission_id: uuid.UUID) -> None:
        """Idempotent: does nothing if the role already carries the permission."""
        await self._session.execute(
            insert(RolePermission)
            .values(id=uuid.uuid4(), role_id=role_id, permission_id=permission_id)
            .on_conflict_do_nothing(index_elements=["role_id", "permission_id"])
        )

    async def remove_permission_from_role(
        self, *, role_id: uuid.UUID, permission_id: uuid.UUID
    ) -> None:
        await self._session.execute(
            delete(RolePermission).where(
                RolePermission.role_id == role_id, RolePermission.permission_id == permission_id
            )
        )

    # ── Account ↔ role ───────────────────────────────────────────────────

    async def get_account_role_names(self, account_id: uuid.UUID) -> list[str]:
        result = await self._session.scalars(
            select(Role.name)
            .join(AccountRole, AccountRole.role_id == Role.id)
            .where(AccountRole.account_id == account_id)
            .order_by(Role.name)
        )
        return list(result)

    async def list_account_roles(
        self, account_id: uuid.UUID, pagination: PaginationParams
    ) -> tuple[list[Role], int]:
        statement = (
            select(Role)
            .join(AccountRole, AccountRole.role_id == Role.id)
            .where(AccountRole.account_id == account_id)
            .order_by(Role.name)
        )
        return await self._paginate(statement, pagination)

    async def add_role_to_account(
        self, *, account_id: uuid.UUID, role_id: uuid.UUID, granted_by: uuid.UUID | None
    ) -> None:
        """Idempotent: does nothing if the account already holds the role."""
        await self._session.execute(
            insert(AccountRole)
            .values(
                id=uuid.uuid4(),
                account_id=account_id,
                role_id=role_id,
                granted_by_account_id=granted_by,
            )
            .on_conflict_do_nothing(index_elements=["account_id", "role_id"])
        )

    async def remove_role_from_account(self, *, account_id: uuid.UUID, role_id: uuid.UUID) -> None:
        await self._session.execute(
            delete(AccountRole).where(
                AccountRole.account_id == account_id, AccountRole.role_id == role_id
            )
        )

    # ── Account ↔ direct permission ──────────────────────────────────────

    async def list_account_direct_permissions(
        self, account_id: uuid.UUID, pagination: PaginationParams
    ) -> tuple[list[Permission], int]:
        statement = (
            select(Permission)
            .join(AccountPermission, AccountPermission.permission_id == Permission.id)
            .where(AccountPermission.account_id == account_id)
            .order_by(Permission.code)
        )
        return await self._paginate(statement, pagination)

    async def add_permission_to_account(
        self, *, account_id: uuid.UUID, permission_id: uuid.UUID, granted_by: uuid.UUID | None
    ) -> None:
        """Idempotent: does nothing if the account already has the direct grant."""
        await self._session.execute(
            insert(AccountPermission)
            .values(
                id=uuid.uuid4(),
                account_id=account_id,
                permission_id=permission_id,
                granted_by_account_id=granted_by,
            )
            .on_conflict_do_nothing(index_elements=["account_id", "permission_id"])
        )

    async def remove_permission_from_account(
        self, *, account_id: uuid.UUID, permission_id: uuid.UUID
    ) -> None:
        await self._session.execute(
            delete(AccountPermission).where(
                AccountPermission.account_id == account_id,
                AccountPermission.permission_id == permission_id,
            )
        )

    # ── Effective permissions ────────────────────────────────────────────

    async def get_account_permission_codes(self, account_id: uuid.UUID) -> list[str]:
        """Every permission the account has: through its roles, or directly."""
        result = await self._session.scalars(
            select(Permission.code).where(self._held_by(account_id)).order_by(Permission.code)
        )
        return list(result)

    async def account_has_permission(self, account_id: uuid.UUID, code: str) -> bool:
        found = await self._session.scalar(
            select(Permission.id).where(Permission.code == code, self._held_by(account_id))
        )
        return found is not None

    @staticmethod
    def _held_by(account_id: uuid.UUID):
        through_roles = (
            select(RolePermission.permission_id)
            .join(AccountRole, AccountRole.role_id == RolePermission.role_id)
            .where(AccountRole.account_id == account_id)
        )
        direct = select(AccountPermission.permission_id).where(
            AccountPermission.account_id == account_id
        )
        return or_(Permission.id.in_(through_roles), Permission.id.in_(direct))

    # ── Helpers ──────────────────────────────────────────────────────────

    async def _paginate(self, statement: Select, pagination: PaginationParams) -> tuple[list, int]:
        total = await self._session.scalar(
            select(func.count()).select_from(statement.order_by(None).subquery())
        )
        rows = await self._session.scalars(
            statement.offset(pagination.offset).limit(pagination.limit)
        )
        return list(rows), total or 0
