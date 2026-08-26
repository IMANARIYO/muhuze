import uuid
from collections.abc import Awaitable, Callable

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.modules.auth.controller import AuthController
from app.modules.auth.exceptions import (
    InsufficientPermissionsError,
    UnauthenticatedError,
)
from app.modules.auth.models import Account
from app.modules.auth.repository import AccountRepository, AuthorizationRepository
from app.modules.auth.service import AuthorizationService

bearer_scheme = HTTPBearer(auto_error=False)


def get_auth_controller(db: AsyncSession = Depends(get_db)) -> AuthController:
    return AuthController(db)


async def get_current_account(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Account:
    """FastAPI dependency other modules use to require and identify the
    caller. Raises UnauthenticatedError (401) on any failure — missing
    header, malformed/expired JWT, or an account that no longer exists or
    was deactivated — without distinguishing which, so a caller can't probe
    for which accounts exist."""
    if credentials is None:
        raise UnauthenticatedError()

    try:
        payload = decode_access_token(credentials.credentials)
        account_id = uuid.UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise UnauthenticatedError() from exc

    account = await AccountRepository(db).get_by_id(account_id)
    if account is None or not account.is_active:
        raise UnauthenticatedError()
    return account


def require_role(*role_names: str) -> Callable[..., Awaitable[Account]]:
    """Dependency factory for other modules: `Depends(require_role("admin"))`.
    Requires the caller to hold at least one of the given roles; raises
    InsufficientPermissionsError (403) otherwise."""

    async def dependency(
        account: Account = Depends(get_current_account),
        db: AsyncSession = Depends(get_db),
    ) -> Account:
        authorization = AuthorizationService(
            AuthorizationRepository(db), AccountRepository(db)
        )
        if not await authorization.has_role(account.id, *role_names):
            raise InsufficientPermissionsError()
        return account

    return dependency


def require_permission(*codes: str) -> Callable[..., Awaitable[Account]]:
    """Dependency factory for other modules: `Depends(require_permission("products.delete"))`.
    Requires the caller to hold at least one of the given permissions."""

    async def dependency(
        account: Account = Depends(get_current_account),
        db: AsyncSession = Depends(get_db),
    ) -> Account:
        authorization = AuthorizationService(
            AuthorizationRepository(db), AccountRepository(db)
        )
        if not await authorization.has_permission(account.id, *codes):
            raise InsufficientPermissionsError()
        return account

    return dependency
