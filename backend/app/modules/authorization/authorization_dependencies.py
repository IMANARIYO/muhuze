"""FastAPI dependencies for roles and permissions.

Other modules protect an endpoint with `require_permission`:

    @router.post("/products")
    async def create_product(
        account: Annotated[Account, Depends(require_permission(PRODUCT_CREATE))],
    ): ...

A missing or invalid token gives 401; a valid account without the permission
gives 403. The permission answers "may this account do this kind of thing?".
Whether a specific resource belongs to the account is still checked in the
service (AGENTS.md §12).
"""

import uuid
from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.permissions import PermissionDefinition
from app.modules.auth.auth_dependencies import get_auth_service, get_current_account
from app.modules.auth.auth_model import Account
from app.modules.auth.auth_service import AuthService
from app.modules.authorization.authorization_exceptions import PermissionDeniedError
from app.modules.authorization.authorization_service import AuthorizationService


def get_authorization_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AuthorizationService:
    return AuthorizationService(session)


def require_permission(
    permission: PermissionDefinition,
) -> Callable[..., Awaitable[Account]]:
    """Dependency factory: the caller must hold `permission`. Returns the caller's account."""

    async def dependency(
        account: Annotated[Account, Depends(get_current_account)],
        service: Annotated[AuthorizationService, Depends(get_authorization_service)],
    ) -> Account:
        if not await service.has_permission(account.id, permission.code):
            raise PermissionDeniedError()
        return account

    return dependency


async def get_target_account(
    account_id: uuid.UUID, auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> Account:
    """The account named in the path; 404 if it doesn't exist."""
    return await auth_service.get_account(account_id)
