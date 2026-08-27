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
    PermissionCreateRequest,
    PermissionResponse,
    PermissionUpdateRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    RoleCreateRequest,
    RoleResponse,
    RoleUpdateRequest,
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

    async def get_my_roles(self, account: Account) -> list[str]:
        return await self.authorization.get_my_roles(account.id)

    async def get_my_permissions(self, account: Account) -> list[str]:
        return await self.authorization.get_my_permissions(account.id)

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

    async def create_role(self, payload: RoleCreateRequest) -> RoleResponse:
        role = await self.authorization.create_role(
            name=payload.name, description=payload.description
        )
        return RoleResponse.model_validate(role)

    async def update_role(
        self, role_name: str, payload: RoleUpdateRequest
    ) -> RoleResponse:
        role = await self.authorization.update_role(
            role_name, name=payload.name, description=payload.description
        )
        return RoleResponse.model_validate(role)

    async def delete_role(self, role_name: str) -> None:
        await self.authorization.delete_role(role_name)

    async def create_permission(
        self, payload: PermissionCreateRequest
    ) -> PermissionResponse:
        permission = await self.authorization.create_permission(
            code=payload.code,
            name=payload.name,
            description=payload.description,
            resource=payload.resource,
            action=payload.action,
        )
        return PermissionResponse.model_validate(permission)

    async def update_permission(
        self, permission_code: str, payload: PermissionUpdateRequest
    ) -> PermissionResponse:
        permission = await self.authorization.update_permission(
            permission_code,
            name=payload.name,
            description=payload.description,
            resource=payload.resource,
            action=payload.action,
        )
        return PermissionResponse.model_validate(permission)

    async def delete_permission(self, permission_code: str) -> None:
        await self.authorization.delete_permission(permission_code)
