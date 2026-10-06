"""Permissions owned by the categories feature."""

from app.core.permissions import PermissionDefinition

CATEGORY_MANAGE = PermissionDefinition(
    code="category.manage",
    name="Manage own categories",
    description=(
        "Create, change, and remove the categories of your own shop and the "
        "attributes their products are described by."
    ),
    # Sellers get it automatically. It only ever reaches the caller's own
    # categories, and the seller must also be active.
    default_roles=("seller",),
)
CATEGORY_MODERATE = PermissionDefinition(
    code="category.moderate",
    name="Moderate categories",
    description="See every shop's categories, and hide or restore one that breaks the rules.",
)

CATEGORY_PERMISSIONS = (CATEGORY_MANAGE, CATEGORY_MODERATE)
