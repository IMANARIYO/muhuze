"""Roles and permissions: who may do what.
Rules are documented in docs/features/003_roles_and_permissions.md.

An account's permissions are those of all its roles plus the ones granted to
it directly. There is no "deny".

Transactions: the methods under "Used by other features" do NOT commit, so
the calling service can make them part of its own transaction (for example,
registration creates the account and gives it the buyer role together).
Every other public method is one unit of work and commits it.
"""

import uuid
from collections.abc import Iterable
from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.permissions import PermissionDefinition
from app.modules.authorization.authorization_constants import SystemRole
from app.modules.authorization.authorization_exceptions import (
    AdminRolePermissionsLockedError,
    OwnAdminRoleRevocationError,
    PermissionNotFoundError,
    RoleNameTakenError,
    RoleNotFoundError,
    SystemRoleProtectedError,
)
from app.modules.authorization.authorization_model import Permission, Role
from app.modules.authorization.authorization_repository import AuthorizationRepository
from app.modules.authorization.authorization_schema import PermissionResponse, RoleResponse
from app.shared.responses.pagination import Page, PaginationParams

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class AccountAuthorization:
    roles: list[str]
    permissions: list[str]


class AuthorizationService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repository = AuthorizationRepository(session)

    # ── Used by other features (no commit) ───────────────────────────────

    async def assign_role(
        self, *, account_id: uuid.UUID, role_name: str, granted_by: uuid.UUID | None = None
    ) -> None:
        """Give a role to an account by role name. Does nothing if the account
        already holds it. Not committed: the caller owns the transaction."""
        role = await self._repository.get_role_by_name(role_name)
        if role is None:
            raise RoleNotFoundError()
        await self._repository.add_role_to_account(
            account_id=account_id, role_id=role.id, granted_by=granted_by
        )

    async def has_permission(self, account_id: uuid.UUID, code: str) -> bool:
        return await self._repository.account_has_permission(account_id, code)

    async def get_account_authorization(self, account_id: uuid.UUID) -> AccountAuthorization:
        return AccountAuthorization(
            roles=await self._repository.get_account_role_names(account_id),
            permissions=await self._repository.get_account_permission_codes(account_id),
        )

    # ── Startup ──────────────────────────────────────────────────────────

    async def sync_permissions(self, definitions: Iterable[PermissionDefinition]) -> None:
        """Make the `permissions` table match the catalog defined in code.

        - A new permission is inserted and given to its default roles.
        - A known permission gets its name and description refreshed. Its
          role assignments are left alone, so an admin's changes survive.
        - A permission that is no longer in the code is deleted, together
          with every grant of it.
        - The admin role ends up holding every permission.
        """
        definitions = list(definitions)
        existing = {p.code: p for p in await self._repository.get_all_permissions()}
        admin = await self._require_role_by_name(SystemRole.ADMIN.value)

        added = []
        for definition in definitions:
            permission = existing.get(definition.code)
            if permission is None:
                permission = Permission(
                    code=definition.code,
                    name=definition.name,
                    description=definition.description,
                    resource=definition.resource,
                    action=definition.action,
                )
                await self._repository.add_permission(permission)
                for role_name in definition.default_roles:
                    role = await self._require_role_by_name(role_name)
                    await self._repository.add_permission_to_role(
                        role_id=role.id, permission_id=permission.id
                    )
                added.append(definition.code)
            else:
                permission.name = definition.name
                permission.description = definition.description
            await self._repository.add_permission_to_role(
                role_id=admin.id, permission_id=permission.id
            )

        current_codes = {definition.code for definition in definitions}
        removed = [code for code in existing if code not in current_codes]
        for code in removed:
            await self._repository.delete_permission(existing[code])

        await self._session.commit()
        if removed:
            logger.warning("permissions removed from the catalog", extra={"codes": removed})
        logger.info(
            "permissions synced",
            extra={"total": len(definitions), "added": len(added), "removed": len(removed)},
        )

    # ── Roles ────────────────────────────────────────────────────────────

    async def list_roles(self, pagination: PaginationParams) -> Page[RoleResponse]:
        roles, total = await self._repository.list_roles(pagination)
        return _role_page(roles, total, pagination)

    async def get_role(self, role_id: uuid.UUID) -> Role:
        role = await self._repository.get_role(role_id)
        if role is None:
            raise RoleNotFoundError()
        return role

    async def create_role(
        self, *, name: str, description: str | None, created_by: uuid.UUID
    ) -> Role:
        if await self._repository.get_role_by_name(name) is not None:
            raise RoleNameTakenError()
        role = Role(name=name, description=description or None)
        try:
            await self._repository.add_role(role)
        except IntegrityError as exc:
            # Lost a race with a concurrent request creating the same name.
            await self._session.rollback()
            raise RoleNameTakenError() from exc
        await self._session.commit()
        logger.info("role created", extra={"role": role.name, "by_account_id": str(created_by)})
        return role

    async def update_role(
        self,
        role_id: uuid.UUID,
        *,
        changes: dict[str, str | None],
        updated_by: uuid.UUID,
    ) -> Role:
        """Apply the given fields (`name`, `description`). A system role can
        have its description changed, but not its name."""
        role = await self.get_role(role_id)
        new_name = changes.get("name")
        if new_name is not None and new_name != role.name:
            if role.is_system:
                raise SystemRoleProtectedError()
            if await self._repository.get_role_by_name(new_name) is not None:
                raise RoleNameTakenError()
            role.name = new_name
        if "description" in changes:
            role.description = changes["description"] or None
        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise RoleNameTakenError() from exc
        logger.info("role updated", extra={"role": role.name, "by_account_id": str(updated_by)})
        return role

    async def delete_role(self, role_id: uuid.UUID, *, deleted_by: uuid.UUID) -> None:
        """Delete a role. Accounts that held it lose the permissions it carried."""
        role = await self.get_role(role_id)
        if role.is_system:
            raise SystemRoleProtectedError()
        name = role.name
        await self._repository.delete_role(role)
        await self._session.commit()
        logger.info("role deleted", extra={"role": name, "by_account_id": str(deleted_by)})

    # ── Permissions of a role ────────────────────────────────────────────

    async def list_permissions(
        self, pagination: PaginationParams, *, resource: str | None
    ) -> Page[PermissionResponse]:
        permissions, total = await self._repository.list_permissions(pagination, resource=resource)
        return _permission_page(permissions, total, pagination)

    async def list_role_permissions(
        self, role_id: uuid.UUID, pagination: PaginationParams
    ) -> Page[PermissionResponse]:
        role = await self.get_role(role_id)
        permissions, total = await self._repository.list_role_permissions(role.id, pagination)
        return _permission_page(permissions, total, pagination)

    async def add_permission_to_role(
        self, role_id: uuid.UUID, permission_code: str, *, changed_by: uuid.UUID
    ) -> None:
        role, permission = await self._editable_role_and_permission(role_id, permission_code)
        await self._repository.add_permission_to_role(role_id=role.id, permission_id=permission.id)
        await self._session.commit()
        logger.info(
            "permission added to role",
            extra={"role": role.name, "code": permission.code, "by_account_id": str(changed_by)},
        )

    async def remove_permission_from_role(
        self, role_id: uuid.UUID, permission_code: str, *, changed_by: uuid.UUID
    ) -> None:
        role, permission = await self._editable_role_and_permission(role_id, permission_code)
        await self._repository.remove_permission_from_role(
            role_id=role.id, permission_id=permission.id
        )
        await self._session.commit()
        logger.info(
            "permission removed from role",
            extra={"role": role.name, "code": permission.code, "by_account_id": str(changed_by)},
        )

    # ── Roles of an account ──────────────────────────────────────────────

    async def list_account_roles(
        self, account_id: uuid.UUID, pagination: PaginationParams
    ) -> Page[RoleResponse]:
        roles, total = await self._repository.list_account_roles(account_id, pagination)
        return _role_page(roles, total, pagination)

    async def grant_role_to_account(
        self, *, account_id: uuid.UUID, role_id: uuid.UUID, granted_by: uuid.UUID
    ) -> None:
        role = await self.get_role(role_id)
        await self._repository.add_role_to_account(
            account_id=account_id, role_id=role.id, granted_by=granted_by
        )
        await self._session.commit()
        logger.info(
            "role granted to account",
            extra={
                "role": role.name,
                "account_id": str(account_id),
                "by_account_id": str(granted_by),
            },
        )

    async def revoke_role_from_account(
        self, *, account_id: uuid.UUID, role_id: uuid.UUID, revoked_by: uuid.UUID
    ) -> None:
        role = await self.get_role(role_id)
        if role.name == SystemRole.ADMIN and account_id == revoked_by:
            # Guards against an admin locking themselves (and possibly
            # everyone) out. Another admin can still do it.
            raise OwnAdminRoleRevocationError()
        await self._repository.remove_role_from_account(account_id=account_id, role_id=role.id)
        await self._session.commit()
        logger.info(
            "role revoked from account",
            extra={
                "role": role.name,
                "account_id": str(account_id),
                "by_account_id": str(revoked_by),
            },
        )

    # ── Direct permissions of an account ─────────────────────────────────

    async def list_account_direct_permissions(
        self, account_id: uuid.UUID, pagination: PaginationParams
    ) -> Page[PermissionResponse]:
        permissions, total = await self._repository.list_account_direct_permissions(
            account_id, pagination
        )
        return _permission_page(permissions, total, pagination)

    async def grant_permission_to_account(
        self, *, account_id: uuid.UUID, permission_code: str, granted_by: uuid.UUID
    ) -> None:
        permission = await self._require_permission_by_code(permission_code)
        await self._repository.add_permission_to_account(
            account_id=account_id, permission_id=permission.id, granted_by=granted_by
        )
        await self._session.commit()
        logger.info(
            "permission granted to account",
            extra={
                "code": permission.code,
                "account_id": str(account_id),
                "by_account_id": str(granted_by),
            },
        )

    async def revoke_permission_from_account(
        self, *, account_id: uuid.UUID, permission_code: str, revoked_by: uuid.UUID
    ) -> None:
        permission = await self._require_permission_by_code(permission_code)
        await self._repository.remove_permission_from_account(
            account_id=account_id, permission_id=permission.id
        )
        await self._session.commit()
        logger.info(
            "permission revoked from account",
            extra={
                "code": permission.code,
                "account_id": str(account_id),
                "by_account_id": str(revoked_by),
            },
        )

    # ── Helpers ──────────────────────────────────────────────────────────

    async def _require_role_by_name(self, name: str) -> Role:
        role = await self._repository.get_role_by_name(name)
        if role is None:
            raise RoleNotFoundError()
        return role

    async def _require_permission_by_code(self, code: str) -> Permission:
        permission = await self._repository.get_permission_by_code(code)
        if permission is None:
            raise PermissionNotFoundError()
        return permission

    async def _editable_role_and_permission(
        self, role_id: uuid.UUID, permission_code: str
    ) -> tuple[Role, Permission]:
        role = await self.get_role(role_id)
        if role.name == SystemRole.ADMIN:
            raise AdminRolePermissionsLockedError()
        return role, await self._require_permission_by_code(permission_code)


def _role_page(roles: list[Role], total: int, pagination: PaginationParams) -> Page[RoleResponse]:
    items = [RoleResponse.model_validate(role) for role in roles]
    return Page[RoleResponse].build(items, total, pagination)


def _permission_page(
    permissions: list[Permission], total: int, pagination: PaginationParams
) -> Page[PermissionResponse]:
    items = [PermissionResponse.model_validate(permission) for permission in permissions]
    return Page[PermissionResponse].build(items, total, pagination)
