"""Permissions owned by the products feature."""

from app.core.permissions import PermissionDefinition

PRODUCT_MANAGE = PermissionDefinition(
    code="product.manage",
    name="Manage own products",
    description="Create, change, publish, archive, and delete the products of your own shop.",
    # Sellers get it automatically. It only ever reaches the caller's own
    # products, and the seller must also be active.
    default_roles=("seller",),
)
PRODUCT_MODERATE = PermissionDefinition(
    code="product.moderate",
    name="Moderate products",
    description=(
        "See every shop's products in any status, and hide or restore one that breaks the rules."
    ),
)

PRODUCT_PERMISSIONS = (PRODUCT_MANAGE, PRODUCT_MODERATE)
