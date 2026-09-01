"""Revenue permissions.

Maps the admin revenue views in app/modules/revenue/router.py: per-order
commission breakdown, order summary, and the platform-wide transaction
list. Aggregated into ALL_PERMISSIONS in app/db/permissions.py.
"""

from app.shared.permissions import PermissionDefinition

REVENUE_PERMISSIONS = [
    PermissionDefinition(
        code="revenue.read",
        name="View revenue",
        resource="revenue",
        action="read",
        description="View per-order breakdowns and all revenue transactions.",
    ),
]
