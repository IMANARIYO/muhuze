"""FastAPI dependencies for authentication.

Other modules protect an endpoint with `Depends(get_current_account)`:

    @router.get("/orders")
    async def list_orders(account: Annotated[Account, Depends(get_current_account)]): ...
"""

from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.auth.auth_constants import USER_AGENT_MAX_LENGTH
from app.modules.auth.auth_model import Account
from app.modules.auth.auth_service import AuthenticatedAccount, AuthService, ClientInfo
from app.modules.authorization.authorization_service import AuthorizationService
from app.shared.exceptions.application_exceptions import AuthenticationError

# auto_error=False: a missing header is reported through the standard error
# envelope (AuthenticationError), not FastAPI's default response.
bearer_scheme = HTTPBearer(auto_error=False, description="The access token from /auth/login")


def get_auth_service(
    request: Request, session: Annotated[AsyncSession, Depends(get_session)]
) -> AuthService:
    state = request.app.state
    return AuthService(
        session=session,
        settings=state.settings,
        password_hasher=state.password_hasher,
        email_sender=state.email_sender,
        authorization=AuthorizationService(session),
    )


def get_client_info(request: Request) -> ClientInfo:
    user_agent = request.headers.get("user-agent")
    return ClientInfo(
        user_agent=user_agent[:USER_AGENT_MAX_LENGTH] if user_agent else None,
        ip_address=request.client.host if request.client else None,
    )


async def get_current_auth(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthenticatedAccount:
    """The caller's account plus the session the access token belongs to."""
    if credentials is None:
        raise AuthenticationError()
    return await service.authenticate(credentials.credentials)


async def get_current_account(
    auth: Annotated[AuthenticatedAccount, Depends(get_current_auth)],
) -> Account:
    return auth.account
