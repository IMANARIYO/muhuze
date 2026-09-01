"""Seller permissions.

Maps the admin-facing seller lifecycle in app/modules/sellers/router.py:
viewing any seller and their documents, and the approve / reject /
suspend / reactivate transitions. Aggregated into ALL_PERMISSIONS in
app/db/permissions.py.
"""

from app.shared.permissions import PermissionDefinition

SELLER_PERMISSIONS = [
    PermissionDefinition(
        code="sellers.read",
        name="View sellers",
        resource="sellers",
        action="read",
        description="List any seller and review their verification documents.",
    ),
    PermissionDefinition(
        code="sellers.approve",
        name="Approve sellers",
        resource="sellers",
        action="approve",
        description="Approve a pending-review seller, activating them.",
    ),
    PermissionDefinition(
        code="sellers.reject",
        name="Reject sellers",
        resource="sellers",
        action="reject",
        description="Reject a pending-review seller with a reason.",
    ),
    PermissionDefinition(
        code="sellers.suspend",
        name="Suspend sellers",
        resource="sellers",
        action="suspend",
        description="Suspend an active seller.",
    ),
    PermissionDefinition(
        code="sellers.reactivate",
        name="Reactivate sellers",
        resource="sellers",
        action="reactivate",
        description="Reactivate a suspended seller.",
    ),
]
