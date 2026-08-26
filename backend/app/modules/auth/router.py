import uuid

from fastapi import APIRouter, Depends, status

from app.modules.auth.controller import AuthController
from app.modules.auth.dependencies import (
    get_auth_controller,
    get_current_account,
    require_role,
)
from app.modules.auth.models import Account
from app.modules.auth.schemas import (
    AssignPermissionRequest,
    AssignRoleRequest,
    EmailVerificationConfirmRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
)
from app.shared.responses.helpers import success_response
from app.shared.responses.schemas import APIResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse:
    account = await controller.register(payload)
    return success_response(data=account, message="Account registered successfully")


@router.post("/login")
async def login(
    payload: LoginRequest,
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse:
    token = await controller.login(payload)
    return success_response(data=token, message="Login successful")


@router.post("/refresh")
async def refresh(
    payload: RefreshTokenRequest,
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse:
    token = await controller.refresh(payload)
    return success_response(data=token, message="Token refreshed successfully")


@router.post("/logout")
async def logout(
    payload: RefreshTokenRequest,
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse:
    await controller.logout(payload)
    return success_response(message="Logged out successfully")


@router.post("/email/verification/request")
async def request_email_verification(
    account: Account = Depends(get_current_account),
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse:
    await controller.request_email_verification(account)
    return success_response(message="Verification code sent")


@router.post("/email/verification/confirm")
async def confirm_email_verification(
    payload: EmailVerificationConfirmRequest,
    account: Account = Depends(get_current_account),
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse:
    await controller.confirm_email_verification(account, payload)
    return success_response(message="Email verified successfully")


@router.post("/password/forgot")
async def forgot_password(
    payload: ForgotPasswordRequest,
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse:
    await controller.forgot_password(payload)
    return success_response(
        message="If that email is registered, a password reset code has been sent"
    )


@router.post("/password/reset")
async def reset_password(
    payload: ResetPasswordRequest,
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse:
    await controller.reset_password(payload)
    return success_response(message="Password reset successfully")


@router.get("/me/authorization")
async def get_my_authorization(
    account: Account = Depends(get_current_account),
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse:
    authorization = await controller.get_my_authorization(account)
    return success_response(
        data=authorization, message="Authorization retrieved successfully"
    )


@router.get("/me/roles")
async def get_my_roles(
    account: Account = Depends(get_current_account),
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse:
    roles = await controller.get_my_roles(account)
    return success_response(data=roles, message="Roles retrieved successfully")


@router.get("/me/permissions")
async def get_my_permissions(
    account: Account = Depends(get_current_account),
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse:
    permissions = await controller.get_my_permissions(account)
    return success_response(
        data=permissions, message="Permissions retrieved successfully"
    )


@router.get("/roles")
async def list_roles(
    admin: Account = Depends(require_role("admin")),
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse:
    roles = await controller.list_roles()
    return success_response(data=roles, message="Roles retrieved successfully")


@router.get("/permissions")
async def list_permissions(
    admin: Account = Depends(require_role("admin")),
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse:
    permissions = await controller.list_permissions()
    return success_response(
        data=permissions, message="Permissions retrieved successfully"
    )


@router.post("/accounts/{account_id}/roles", status_code=status.HTTP_201_CREATED)
async def assign_role_to_account(
    account_id: uuid.UUID,
    payload: AssignRoleRequest,
    admin: Account = Depends(require_role("admin")),
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse:
    await controller.assign_role_to_account(account_id, payload)
    return success_response(message="Role assigned successfully")


@router.delete("/accounts/{account_id}/roles/{role_name}")
async def revoke_role_from_account(
    account_id: uuid.UUID,
    role_name: str,
    admin: Account = Depends(require_role("admin")),
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse:
    await controller.revoke_role_from_account(account_id, role_name)
    return success_response(message="Role revoked successfully")


@router.get("/accounts/{account_id}/roles")
async def list_roles_for_account(
    account_id: uuid.UUID,
    admin: Account = Depends(require_role("admin")),
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse:
    roles = await controller.list_roles_for_account(account_id)
    return success_response(data=roles, message="Account roles retrieved successfully")


@router.get("/roles/{role_name}/permissions")
async def list_permissions_for_role(
    role_name: str,
    admin: Account = Depends(require_role("admin")),
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse:
    permissions = await controller.list_permissions_for_role(role_name)
    return success_response(
        data=permissions, message="Role permissions retrieved successfully"
    )


@router.post("/roles/{role_name}/permissions", status_code=status.HTTP_201_CREATED)
async def assign_permission_to_role(
    role_name: str,
    payload: AssignPermissionRequest,
    admin: Account = Depends(require_role("admin")),
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse:
    await controller.assign_permission_to_role(role_name, payload)
    return success_response(message="Permission assigned to role successfully")


@router.delete("/roles/{role_name}/permissions/{permission_code}")
async def revoke_permission_from_role(
    role_name: str,
    permission_code: str,
    admin: Account = Depends(require_role("admin")),
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse:
    await controller.revoke_permission_from_role(role_name, permission_code)
    return success_response(message="Permission revoked from role successfully")


@router.get("/accounts/{account_id}/permissions")
async def list_direct_permissions(
    account_id: uuid.UUID,
    admin: Account = Depends(require_role("admin")),
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse:
    permissions = await controller.list_direct_permissions(account_id)
    return success_response(
        data=permissions, message="Direct permissions retrieved successfully"
    )


@router.post("/accounts/{account_id}/permissions", status_code=status.HTTP_201_CREATED)
async def grant_direct_permission(
    account_id: uuid.UUID,
    payload: AssignPermissionRequest,
    admin: Account = Depends(require_role("admin")),
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse:
    await controller.grant_direct_permission(account_id, payload)
    return success_response(message="Permission granted directly to account")


@router.delete("/accounts/{account_id}/permissions/{permission_code}")
async def revoke_direct_permission(
    account_id: uuid.UUID,
    permission_code: str,
    admin: Account = Depends(require_role("admin")),
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse:
    await controller.revoke_direct_permission(account_id, permission_code)
    return success_response(message="Direct permission revoked from account")
