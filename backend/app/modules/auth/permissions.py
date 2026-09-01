"""Auth / user-access permissions.

Maps the account, role, and permission administration surface in
app/modules/auth/router.py — exactly what the admin "Users & access"
workspace drives. Aggregated into ALL_PERMISSIONS in app/db/permissions.py.

These describe the capability to manage other accounts' access, not the
ability to exercise a specific business action (those live in the owning
module's permissions.py — e.g. sellers.approve in
app/modules/sellers/permissions.py).
"""

from app.shared.permissions import PermissionDefinition

AUTH_PERMISSIONS = [
    PermissionDefinition(
        code="accounts.read",
        name="View accounts",
        resource="accounts",
        action="read",
        description="List all accounts and their assigned roles.",
    ),
    PermissionDefinition(
        code="accounts.manage_roles",
        name="Manage account roles",
        resource="accounts",
        action="manage_roles",
        description="Assign and revoke roles on any account.",
    ),
    PermissionDefinition(
        code="accounts.manage_permissions",
        name="Manage account permissions",
        resource="accounts",
        action="manage_permissions",
        description="Grant and revoke direct permissions on any account.",
    ),
    PermissionDefinition(
        code="roles.manage",
        name="Manage roles",
        resource="roles",
        action="manage",
        description="Create, update, delete roles and assign permissions to them.",
    ),
    PermissionDefinition(
        code="permissions.manage",
        name="Manage permissions",
        resource="permissions",
        action="manage",
        description="Create, update, delete permission definitions.",
    ),
]
