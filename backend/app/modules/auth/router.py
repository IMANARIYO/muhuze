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
from app.shared.responses.helpers import success_response
from app.shared.responses.schemas import APIResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse[AccountResponse]:
    """Create a new account with email + password. The account starts
    unverified — see /email/verification/request to verify it."""
    account = await controller.register(payload)
    return success_response(data=account, message="Account registered successfully")


@router.post("/login")
async def login(
    payload: LoginRequest,
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse[TokenResponse]:
    """Exchange email + password for an access/refresh token pair."""
    token = await controller.login(payload)
    return success_response(data=token, message="Login successful")


@router.post("/refresh")
async def refresh(
    payload: RefreshTokenRequest,
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse[TokenResponse]:
    """Exchange a valid refresh token for a new access/refresh token pair.
    The old refresh token is invalidated (rotation)."""
    token = await controller.refresh(payload)
    return success_response(data=token, message="Token refreshed successfully")


@router.post("/logout")
async def logout(
    payload: RefreshTokenRequest,
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse[None]:
    """Invalidate a refresh token, ending that session."""
    await controller.logout(payload)
    return success_response(message="Logged out successfully")


@router.post("/email/verification/request")
async def request_email_verification(
    account: Account = Depends(get_current_account),
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse[None]:
    """Send a verification code to the caller's own email address."""
    await controller.request_email_verification(account)
    return success_response(message="Verification code sent")


@router.post("/email/verification/confirm")
async def confirm_email_verification(
    payload: EmailVerificationConfirmRequest,
    account: Account = Depends(get_current_account),
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse[None]:
    """Confirm the code sent by /email/verification/request, marking the
    caller's account as verified."""
    await controller.confirm_email_verification(account, payload)
    return success_response(message="Email verified successfully")


@router.post("/password/forgot")
async def forgot_password(
    payload: ForgotPasswordRequest,
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse[None]:
    """Request a password reset code by email. Always returns success
    regardless of whether the email is registered, to avoid leaking which
    emails have accounts."""
    await controller.forgot_password(payload)
    return success_response(
        message="If that email is registered, a password reset code has been sent"
    )


@router.post("/password/reset")
async def reset_password(
    payload: ResetPasswordRequest,
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse[None]:
    """Set a new password using the token from /password/forgot. All of
    the account's existing refresh tokens are invalidated."""
    await controller.reset_password(payload)
    return success_response(message="Password reset successfully")


@router.get("/me/authorization")
async def get_my_authorization(
    account: Account = Depends(get_current_account),
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse[AuthorizationResponse]:
    """The caller's own roles and effective permission codes in one call —
    convenient for a frontend building its own UI permission checks."""
    authorization = await controller.get_my_authorization(account)
    return success_response(
        data=authorization, message="Authorization retrieved successfully"
    )


@router.get("/me/roles")
async def get_my_roles(
    account: Account = Depends(get_current_account),
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse[list[str]]:
    """The caller's own role names."""
    roles = await controller.get_my_roles(account)
    return success_response(data=roles, message="Roles retrieved successfully")


@router.get("/me/permissions")
async def get_my_permissions(
    account: Account = Depends(get_current_account),
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse[list[str]]:
    """The caller's own effective permission codes (from roles and any
    direct grants combined)."""
    permissions = await controller.get_my_permissions(account)
    return success_response(
        data=permissions, message="Permissions retrieved successfully"
    )


@router.get("/roles")
async def list_roles(
    admin: Account = Depends(require_role("admin")),
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse[list[RoleResponse]]:
    """List every role defined in the system. Admin only."""
    roles = await controller.list_roles()
    return success_response(data=roles, message="Roles retrieved successfully")


@router.get("/permissions")
async def list_permissions(
    admin: Account = Depends(require_role("admin")),
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse[list[PermissionResponse]]:
    """List every permission defined in the system. Admin only."""
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
) -> APIResponse[None]:
    """Grant a role to an account. Admin only."""
    await controller.assign_role_to_account(account_id, payload)
    return success_response(message="Role assigned successfully")


@router.delete("/accounts/{account_id}/roles/{role_name}")
async def revoke_role_from_account(
    account_id: uuid.UUID,
    role_name: str,
    admin: Account = Depends(require_role("admin")),
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse[None]:
    """Revoke a role from an account. Admin only."""
    await controller.revoke_role_from_account(account_id, role_name)
    return success_response(message="Role revoked successfully")


@router.get("/accounts/{account_id}/roles")
async def list_roles_for_account(
    account_id: uuid.UUID,
    admin: Account = Depends(require_role("admin")),
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse[list[RoleResponse]]:
    """List the roles held by a specific account. Admin only."""
    roles = await controller.list_roles_for_account(account_id)
    return success_response(data=roles, message="Account roles retrieved successfully")


@router.get("/roles/{role_name}/permissions")
async def list_permissions_for_role(
    role_name: str,
    admin: Account = Depends(require_role("admin")),
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse[list[PermissionResponse]]:
    """List the permissions granted by a specific role. Admin only."""
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
) -> APIResponse[None]:
    """Add a permission to a role, granting it to every account holding
    that role. Admin only."""
    await controller.assign_permission_to_role(role_name, payload)
    return success_response(message="Permission assigned to role successfully")


@router.delete("/roles/{role_name}/permissions/{permission_code}")
async def revoke_permission_from_role(
    role_name: str,
    permission_code: str,
    admin: Account = Depends(require_role("admin")),
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse[None]:
    """Remove a permission from a role. Admin only."""
    await controller.revoke_permission_from_role(role_name, permission_code)
    return success_response(message="Permission revoked from role successfully")


@router.get("/accounts/{account_id}/permissions")
async def list_direct_permissions(
    account_id: uuid.UUID,
    admin: Account = Depends(require_role("admin")),
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse[list[str]]:
    """List permissions granted directly to an account, bypassing its
    roles. Admin only."""
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
) -> APIResponse[None]:
    """Grant a permission directly to an account, independent of its
    roles — use sparingly, prefer roles for anything reusable. Admin only."""
    await controller.grant_direct_permission(account_id, payload)
    return success_response(message="Permission granted directly to account")


@router.delete("/accounts/{account_id}/permissions/{permission_code}")
async def revoke_direct_permission(
    account_id: uuid.UUID,
    permission_code: str,
    admin: Account = Depends(require_role("admin")),
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse[None]:
    """Revoke a directly-granted permission from an account. Does not
    affect permissions the account holds via a role. Admin only."""
    await controller.revoke_direct_permission(account_id, permission_code)
    return success_response(message="Direct permission revoked from account")


# --- role CRUD ---------------------------------------------------------------


@router.post("/roles", status_code=status.HTTP_201_CREATED)
async def create_role(
    payload: RoleCreateRequest,
    admin: Account = Depends(require_role("admin")),
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse[RoleResponse]:
    """Create a new role. The role name must be unique. Admin only."""
    role = await controller.create_role(payload)
    return success_response(data=role, message="Role created successfully")


@router.patch("/roles/{role_name}")
async def update_role(
    role_name: str,
    payload: RoleUpdateRequest,
    admin: Account = Depends(require_role("admin")),
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse[RoleResponse]:
    """Update a role's name or description. Admin only."""
    role = await controller.update_role(role_name, payload)
    return success_response(data=role, message="Role updated successfully")


@router.delete("/roles/{role_name}")
async def delete_role(
    role_name: str,
    admin: Account = Depends(require_role("admin")),
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse[None]:
    """Delete a role. Any accounts holding this role will lose its
    permissions. Admin only."""
    await controller.delete_role(role_name)
    return success_response(message="Role deleted successfully")


# --- permission CRUD ---------------------------------------------------------


@router.post("/permissions", status_code=status.HTTP_201_CREATED)
async def create_permission(
    payload: PermissionCreateRequest,
    admin: Account = Depends(require_role("admin")),
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse[PermissionResponse]:
    """Create a new permission. The code must be unique. Admin only."""
    permission = await controller.create_permission(payload)
    return success_response(data=permission, message="Permission created successfully")


@router.patch("/permissions/{permission_code}")
async def update_permission(
    permission_code: str,
    payload: PermissionUpdateRequest,
    admin: Account = Depends(require_role("admin")),
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse[PermissionResponse]:
    """Update a permission's name, description, resource, or action. Admin
    only."""
    permission = await controller.update_permission(permission_code, payload)
    return success_response(data=permission, message="Permission updated successfully")


@router.delete("/permissions/{permission_code}")
async def delete_permission(
    permission_code: str,
    admin: Account = Depends(require_role("admin")),
    controller: AuthController = Depends(get_auth_controller),
) -> APIResponse[None]:
    """Delete a permission. Any roles holding this permission will lose it.
    Admin only."""
    await controller.delete_permission(permission_code)
    return success_response(message="Permission deleted successfully")
