"""Permissions owned by the roles and permissions feature.

None has a default role: only `admin`, which holds every permission, can
manage access until an admin decides otherwise.
"""

from app.core.permissions import PermissionDefinition

ROLE_READ = PermissionDefinition(
    code="role.read",
    name="View roles",
    description="See roles, the permissions each role carries, and which accounts hold them.",
)
ROLE_MANAGE = PermissionDefinition(
    code="role.manage",
    name="Manage roles",
    description="Create, rename, and delete roles, and change the permissions a role carries.",
)
ROLE_ASSIGN = PermissionDefinition(
    code="role.assign",
    name="Assign roles to accounts",
    description="Give a role to an account or take it away.",
)
PERMISSION_READ = PermissionDefinition(
    code="permission.read",
    name="View permissions",
    description="See the catalog of permissions and the ones granted directly to an account.",
)
PERMISSION_GRANT = PermissionDefinition(
    code="permission.grant",
    name="Grant permissions to accounts",
    description="Give one permission directly to one account, or take it away.",
)

AUTHORIZATION_PERMISSIONS = (
    ROLE_READ,
    ROLE_MANAGE,
    ROLE_ASSIGN,
    PERMISSION_READ,
    PERMISSION_GRANT,
)
