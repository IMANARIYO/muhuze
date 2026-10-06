from app.shared.exceptions.application_exceptions import (
    AuthorizationError,
    BusinessRuleError,
    ConflictError,
    NotFoundError,
)


class PermissionDeniedError(AuthorizationError):
    message = "You do not have permission to perform this action"


class RoleNotFoundError(NotFoundError):
    message = "Role not found"


class PermissionNotFoundError(NotFoundError):
    message = "Permission not found"


class RoleNameTakenError(ConflictError):
    message = "A role with this name already exists"


class SystemRoleProtectedError(BusinessRuleError):
    message = "System roles cannot be renamed or deleted"


class AdminRolePermissionsLockedError(BusinessRuleError):
    message = "The admin role always holds every permission"


class OwnAdminRoleRevocationError(BusinessRuleError):
    message = "You cannot remove the admin role from your own account"
