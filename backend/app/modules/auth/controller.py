import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import Account
from app.modules.auth.repository import (
    AccountRepository,
    AuthorizationRepository,
    PasswordResetTokenRepository,
    RefreshTokenRepository,
    VerificationCodeRepository,
)
from app.modules.auth.schemas import (
    AccountResponse,
    AssignPermissionRequest,
    AssignRoleRequest,
    AuthorizationResponse,
    EmailVerificationConfirmRequest,
    ForgotPasswordRequest,
    LoginRequest,
    PermissionResponse,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    RoleResponse,
    TokenResponse,
)
from app.modules.auth.service import (
    AuthorizationService,
    AuthService,
    PasswordResetService,
    VerificationService,
)


class AuthController:
    """Translates HTTP requests/responses to and from the auth services."""

    def __init__(self, db: AsyncSession) -> None:
        accounts = AccountRepository(db)
        refresh_tokens = RefreshTokenRepository(db)
        authorization_repo = AuthorizationRepository(db)

        self.auth = AuthService(accounts, refresh_tokens, authorization_repo)
        self.verification = VerificationService(
            accounts, VerificationCodeRepository(db)
        )
        self.password_reset = PasswordResetService(
            accounts, PasswordResetTokenRepository(db), refresh_tokens
        )
        self.authorization = AuthorizationService(authorization_repo, accounts)

    async def register(self, payload: RegisterRequest) -> AccountResponse:
        account = await self.auth.register(
            email=payload.email,
            phone=payload.phone,
            password=payload.password,
        )
        return AccountResponse.model_validate(account)

    async def login(self, payload: LoginRequest) -> TokenResponse:
        access_token, refresh_token = await self.auth.login(
            email=payload.email, password=payload.password
        )
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    async def refresh(self, payload: RefreshTokenRequest) -> TokenResponse:
        access_token, refresh_token = await self.auth.refresh(
            raw_refresh_token=payload.refresh_token
        )
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    async def logout(self, payload: RefreshTokenRequest) -> None:
        await self.auth.logout(raw_refresh_token=payload.refresh_token)

    async def request_email_verification(self, account: Account) -> None:
        await self.verification.request_email_verification(account)

    async def confirm_email_verification(
        self, account: Account, payload: EmailVerificationConfirmRequest
    ) -> None:
        await self.verification.confirm_email_verification(account, code=payload.code)

    async def forgot_password(self, payload: ForgotPasswordRequest) -> None:
        await self.password_reset.request_password_reset(email=payload.email)

    async def reset_password(self, payload: ResetPasswordRequest) -> None:
        await self.password_reset.reset_password(
            raw_token=payload.token, new_password=payload.new_password
        )

    async def get_my_authorization(self, account: Account) -> AuthorizationResponse:
        roles, permissions = await self.authorization.get_my_authorization(account.id)
        return AuthorizationResponse(roles=roles, permissions=permissions)

    async def list_roles(self) -> list[RoleResponse]:
        roles = await self.authorization.list_roles()
        return [RoleResponse.model_validate(role) for role in roles]

    async def list_permissions(self) -> list[PermissionResponse]:
        permissions = await self.authorization.list_permissions()
        return [
            PermissionResponse.model_validate(permission) for permission in permissions
        ]

    async def assign_role_to_account(
        self, account_id: uuid.UUID, payload: AssignRoleRequest
    ) -> None:
        await self.authorization.assign_role_to_account(account_id, payload.role_name)

    async def revoke_role_from_account(
        self, account_id: uuid.UUID, role_name: str
    ) -> None:
        await self.authorization.revoke_role_from_account(account_id, role_name)

    async def list_roles_for_account(self, account_id: uuid.UUID) -> list[RoleResponse]:
        roles = await self.authorization.list_roles_for_account(account_id)
        return [RoleResponse.model_validate(role) for role in roles]

    async def list_permissions_for_role(
        self, role_name: str
    ) -> list[PermissionResponse]:
        permissions = await self.authorization.list_permissions_for_role(role_name)
        return [
            PermissionResponse.model_validate(permission) for permission in permissions
        ]

    async def assign_permission_to_role(
        self, role_name: str, payload: AssignPermissionRequest
    ) -> None:
        await self.authorization.assign_permission_to_role(
            role_name, payload.permission_code
        )

    async def revoke_permission_from_role(
        self, role_name: str, permission_code: str
    ) -> None:
        await self.authorization.revoke_permission_from_role(role_name, permission_code)

    async def grant_direct_permission(
        self, account_id: uuid.UUID, payload: AssignPermissionRequest
    ) -> None:
        await self.authorization.grant_direct_permission(
            account_id, payload.permission_code
        )

    async def revoke_direct_permission(
        self, account_id: uuid.UUID, permission_code: str
    ) -> None:
        await self.authorization.revoke_direct_permission(account_id, permission_code)

    async def list_direct_permissions(self, account_id: uuid.UUID) -> list[str]:
        return await self.authorization.list_direct_permissions(account_id)
