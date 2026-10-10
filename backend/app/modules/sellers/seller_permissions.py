"""Permissions owned by the sellers feature.

A seller managing their OWN application needs no permission, only a login:
those endpoints act on the caller's own seller record. The permissions below
are for staff acting on OTHER people's applications. None has a default
role, so only `admin` holds them until an admin decides otherwise.
"""

from app.core.permissions import PermissionDefinition

SELLER_READ = PermissionDefinition(
    code="seller.read",
    name="View seller applications",
    description=(
        "See every seller, their application details, identity document number, "
        "uploaded documents, and status history."
    ),
)
SELLER_REVIEW = PermissionDefinition(
    code="seller.review",
    name="Review seller applications",
    description="Approve or reject a seller application that is waiting for review.",
)
SELLER_SUSPEND = PermissionDefinition(
    code="seller.suspend",
    name="Suspend sellers",
    description="Suspend an active seller, and reinstate a suspended one.",
)

SELLER_PERMISSIONS = (SELLER_READ, SELLER_REVIEW, SELLER_SUSPEND)
