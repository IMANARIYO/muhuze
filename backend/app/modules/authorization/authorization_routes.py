import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.modules.auth.auth_dependencies import get_current_account
from app.modules.auth.auth_model import Account
from app.modules.authorization.authorization_dependencies import (
    get_authorization_service,
    get_target_account,
    require_permission,
)
from app.modules.authorization.authorization_permissions import (
    PERMISSION_GRANT,
    PERMISSION_READ,
    ROLE_ASSIGN,
    ROLE_MANAGE,
    ROLE_READ,
)
from app.modules.authorization.authorization_schema import (
    AccountAuthorizationResponse,
    PermissionFilters,
    PermissionResponse,
    RoleCreateRequest,
    RoleResponse,
    RoleUpdateRequest,
)
from app.modules.authorization.authorization_service import AuthorizationService
from app.shared.responses.api_response import APIResponse, success_response
from app.shared.responses.pagination import Page, PaginationParams

authorization_router = APIRouter(tags=["Roles and permissions"])

ServiceDep = Annotated[AuthorizationService, Depends(get_authorization_service)]
# Depends(), not Query(): FastAPI accepts only ONE Query() parameter model per
# endpoint, and list endpoints here combine pagination with filters.
PaginationDep = Annotated[PaginationParams, Depends()]
CurrentAccountDep = Annotated[Account, Depends(get_current_account)]
# In a signature, always list the permission check BEFORE the target account:
# dependencies run in order, and a caller without access must get 401/403
# before learning whether the account exists.
TargetAccountDep = Annotated[Account, Depends(get_target_account)]
PermissionCode = Annotated[str, "A permission code, e.g. product.create"]


def allowed(permission) -> type[Account]:
    return Annotated[Account, Depends(require_permission(permission))]


# ── The caller's own access ──────────────────────────────────────────────


@authorization_router.get(
    "/authorization/me", response_model=APIResponse[AccountAuthorizationResponse]
)
async def get_my_authorization(account: CurrentAccountDep, service: ServiceDep) -> JSONResponse:
    """The caller's roles and every permission they have. A frontend uses the
    permission codes to decide what to show; the API still checks each request."""
    authorization = await service.get_account_authorization(account.id)
    return success_response(
        data=AccountAuthorizationResponse.model_validate(authorization),
        message="Authorization retrieved",
    )


# ── Roles ────────────────────────────────────────────────────────────────


@authorization_router.get("/roles", response_model=APIResponse[Page[RoleResponse]])
async def list_roles(
    pagination: PaginationDep, service: ServiceDep, _: allowed(ROLE_READ)
) -> JSONResponse:
    """Every role, ordered by name."""
    return success_response(data=await service.list_roles(pagination), message="Roles retrieved")


@authorization_router.post(
    "/roles", response_model=APIResponse[RoleResponse], status_code=status.HTTP_201_CREATED
)
async def create_role(
    payload: RoleCreateRequest, service: ServiceDep, admin: allowed(ROLE_MANAGE)
) -> JSONResponse:
    """Create a role. It carries no permissions until some are added."""
    role = await service.create_role(
        name=payload.name, description=payload.description, created_by=admin.id
    )
    return success_response(
        data=RoleResponse.model_validate(role),
        message="Role created",
        status_code=status.HTTP_201_CREATED,
    )


@authorization_router.get("/roles/{role_id}", response_model=APIResponse[RoleResponse])
async def get_role(role_id: uuid.UUID, service: ServiceDep, _: allowed(ROLE_READ)) -> JSONResponse:
    role = await service.get_role(role_id)
    return success_response(data=RoleResponse.model_validate(role), message="Role retrieved")


@authorization_router.patch("/roles/{role_id}", response_model=APIResponse[RoleResponse])
async def update_role(
    role_id: uuid.UUID,
    payload: RoleUpdateRequest,
    service: ServiceDep,
    admin: allowed(ROLE_MANAGE),
) -> JSONResponse:
    """Change a role's name or description. System roles keep their name."""
    role = await service.update_role(
        role_id, changes=payload.model_dump(exclude_unset=True), updated_by=admin.id
    )
    return success_response(data=RoleResponse.model_validate(role), message="Role updated")


@authorization_router.delete("/roles/{role_id}", response_model=APIResponse[None])
async def delete_role(
    role_id: uuid.UUID, service: ServiceDep, admin: allowed(ROLE_MANAGE)
) -> JSONResponse:
    """Delete a role. Accounts that held it lose the permissions it carried.
    System roles cannot be deleted."""
    await service.delete_role(role_id, deleted_by=admin.id)
    return success_response(message="Role deleted")


# ── Permissions ──────────────────────────────────────────────────────────


@authorization_router.get("/permissions", response_model=APIResponse[Page[PermissionResponse]])
async def list_permissions(
    pagination: PaginationDep,
    filters: Annotated[PermissionFilters, Depends()],
    service: ServiceDep,
    _: allowed(PERMISSION_READ),
) -> JSONResponse:
    """The permission catalog, ordered by code. Permissions are defined by the
    system; they can be assigned but not created or edited."""
    page = await service.list_permissions(pagination, resource=filters.resource)
    return success_response(data=page, message="Permissions retrieved")


@authorization_router.get(
    "/roles/{role_id}/permissions", response_model=APIResponse[Page[PermissionResponse]]
)
async def list_role_permissions(
    role_id: uuid.UUID, pagination: PaginationDep, service: ServiceDep, _: allowed(ROLE_READ)
) -> JSONResponse:
    """The permissions a role carries."""
    page = await service.list_role_permissions(role_id, pagination)
    return success_response(data=page, message="Role permissions retrieved")


@authorization_router.put(
    "/roles/{role_id}/permissions/{permission_code}", response_model=APIResponse[None]
)
async def add_permission_to_role(
    role_id: uuid.UUID,
    permission_code: PermissionCode,
    service: ServiceDep,
    admin: allowed(ROLE_MANAGE),
) -> JSONResponse:
    """Add a permission to a role. Every account holding the role gets it."""
    await service.add_permission_to_role(role_id, permission_code, changed_by=admin.id)
    return success_response(message="Permission added to role")


@authorization_router.delete(
    "/roles/{role_id}/permissions/{permission_code}", response_model=APIResponse[None]
)
async def remove_permission_from_role(
    role_id: uuid.UUID,
    permission_code: PermissionCode,
    service: ServiceDep,
    admin: allowed(ROLE_MANAGE),
) -> JSONResponse:
    """Remove a permission from a role."""
    await service.remove_permission_from_role(role_id, permission_code, changed_by=admin.id)
    return success_response(message="Permission removed from role")


# ── Roles of an account ──────────────────────────────────────────────────


@authorization_router.get(
    "/accounts/{account_id}/roles", response_model=APIResponse[Page[RoleResponse]]
)
async def list_account_roles(
    _: allowed(ROLE_READ), target: TargetAccountDep, pagination: PaginationDep, service: ServiceDep
) -> JSONResponse:
    """The roles an account holds."""
    page = await service.list_account_roles(target.id, pagination)
    return success_response(data=page, message="Account roles retrieved")


@authorization_router.put(
    "/accounts/{account_id}/roles/{role_id}", response_model=APIResponse[None]
)
async def grant_role_to_account(
    admin: allowed(ROLE_ASSIGN),
    target: TargetAccountDep,
    role_id: uuid.UUID,
    service: ServiceDep,
) -> JSONResponse:
    """Give a role to an account."""
    await service.grant_role_to_account(account_id=target.id, role_id=role_id, granted_by=admin.id)
    return success_response(message="Role granted")


@authorization_router.delete(
    "/accounts/{account_id}/roles/{role_id}", response_model=APIResponse[None]
)
async def revoke_role_from_account(
    admin: allowed(ROLE_ASSIGN),
    target: TargetAccountDep,
    role_id: uuid.UUID,
    service: ServiceDep,
) -> JSONResponse:
    """Take a role away from an account. An admin cannot remove their own admin role."""
    await service.revoke_role_from_account(
        account_id=target.id, role_id=role_id, revoked_by=admin.id
    )
    return success_response(message="Role revoked")


# ── Direct permissions of an account ─────────────────────────────────────


@authorization_router.get(
    "/accounts/{account_id}/permissions", response_model=APIResponse[Page[PermissionResponse]]
)
async def list_account_direct_permissions(
    _: allowed(PERMISSION_READ),
    target: TargetAccountDep,
    pagination: PaginationDep,
    service: ServiceDep,
) -> JSONResponse:
    """Permissions granted directly to an account. Those it has through its
    roles are not listed here."""
    page = await service.list_account_direct_permissions(target.id, pagination)
    return success_response(data=page, message="Account permissions retrieved")


@authorization_router.put(
    "/accounts/{account_id}/permissions/{permission_code}", response_model=APIResponse[None]
)
async def grant_permission_to_account(
    admin: allowed(PERMISSION_GRANT),
    target: TargetAccountDep,
    permission_code: PermissionCode,
    service: ServiceDep,
) -> JSONResponse:
    """Grant one permission directly to one account, outside of any role."""
    await service.grant_permission_to_account(
        account_id=target.id, permission_code=permission_code, granted_by=admin.id
    )
    return success_response(message="Permission granted")


@authorization_router.delete(
    "/accounts/{account_id}/permissions/{permission_code}", response_model=APIResponse[None]
)
async def revoke_permission_from_account(
    admin: allowed(PERMISSION_GRANT),
    target: TargetAccountDep,
    permission_code: PermissionCode,
    service: ServiceDep,
) -> JSONResponse:
    """Remove a direct grant. Permissions the account has through a role stay."""
    await service.revoke_permission_from_account(
        account_id=target.id, permission_code=permission_code, revoked_by=admin.id
    )
    return success_response(message="Permission revoked")
