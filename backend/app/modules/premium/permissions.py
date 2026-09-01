"""Premium plan permissions.

Maps the admin-side premium surface in app/modules/premium/router.py:
creating/updating plans (where commission rates are set) and viewing all
seller subscriptions. Aggregated into ALL_PERMISSIONS in
app/db/permissions.py.
"""

from app.shared.permissions import PermissionDefinition

PREMIUM_PERMISSIONS = [
    PermissionDefinition(
        code="premium.manage",
        name="Manage premium plans",
        resource="premium",
        action="manage",
        description="Create and update premium plans and view all subscriptions.",
    ),
]
