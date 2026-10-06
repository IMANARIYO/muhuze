"""Work done once, when the application starts and before it serves requests.

Each task is idempotent: running it again changes nothing. The database must
be migrated first (`uv run alembic upgrade head`); otherwise startup fails.
"""

from fastapi import FastAPI

from app.core.logging import get_logger
from app.core.permission_registry import ALL_PERMISSIONS
from app.modules.auth.auth_service import AuthService
from app.modules.authorization.authorization_constants import SystemRole
from app.modules.authorization.authorization_service import AuthorizationService

logger = get_logger(__name__)


async def run_startup_tasks(app: FastAPI) -> None:
    state = app.state
    settings = state.settings
    async with state.session_factory() as session:
        authorization = AuthorizationService(session)
        # 1. The permission catalog defined in code becomes rows admins can assign.
        await authorization.sync_permissions(ALL_PERMISSIONS)

        # 2. The first admin: without one, nobody could grant the admin role.
        if settings.bootstrap_admin_email is None:
            return
        auth = AuthService(
            session=session,
            settings=settings,
            password_hasher=state.password_hasher,
            email_sender=state.email_sender,
            authorization=authorization,
        )
        account, created = await auth.ensure_verified_account(
            email=settings.bootstrap_admin_email,
            password=settings.bootstrap_admin_password.get_secret_value(),
            full_name=settings.bootstrap_admin_full_name,
        )
        await authorization.assign_role(account_id=account.id, role_name=SystemRole.ADMIN.value)
        await session.commit()
        logger.info(
            "bootstrap admin ensured",
            extra={"account_id": str(account.id), "newly_created": created},
        )
