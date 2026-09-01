"""Product-related permissions.

Covers the admin-facing catalog moderation and curated vocabularies in
app/modules/products/router.py: product, brand, attribute, and seller
listing lifecycle actions. Seller self-service endpoints that let the
owning seller act on their own rows are intentionally not listed here —
they're gated by ownership + active-seller rules, not by a permission.

Aggregated into ALL_PERMISSIONS in app/db/permissions.py.
"""

from app.shared.permissions import PermissionDefinition

PRODUCT_PERMISSIONS = [
    PermissionDefinition(
        code="products.approve",
        name="Approve products",
        resource="products",
        action="approve",
        description="Approve a pending-review product, activating it.",
    ),
    PermissionDefinition(
        code="products.reject",
        name="Reject products",
        resource="products",
        action="reject",
        description="Reject a pending-review product with a reason.",
    ),
    PermissionDefinition(
        code="products.archive",
        name="Archive products",
        resource="products",
        action="archive",
        description="Archive an active product, removing it from the catalog.",
    ),
    PermissionDefinition(
        code="listings.approve",
        name="Approve listings",
        resource="listings",
        action="approve",
        description="Approve a seller listing, putting it on sale.",
    ),
    PermissionDefinition(
        code="listings.reject",
        name="Reject listings",
        resource="listings",
        action="reject",
        description="Reject a seller listing with a reason.",
    ),
    PermissionDefinition(
        code="listings.suspend",
        name="Suspend listings",
        resource="listings",
        action="suspend",
        description="Suspend an active listing.",
    ),
    PermissionDefinition(
        code="listings.reactivate",
        name="Reactivate listings",
        resource="listings",
        action="reactivate",
        description="Reactivate a suspended listing.",
    ),
    PermissionDefinition(
        code="brands.create",
        name="Create brands",
        resource="brands",
        action="create",
        description="Create a brand in the curated brand vocabulary.",
    ),
    PermissionDefinition(
        code="brands.update",
        name="Update brands",
        resource="brands",
        action="update",
        description="Update a brand's name, description, or status.",
    ),
    PermissionDefinition(
        code="attributes.create",
        name="Create attributes",
        resource="attributes",
        action="create",
        description="Create an attribute definition variants are built from.",
    ),
    PermissionDefinition(
        code="attributes.update",
        name="Update attributes",
        resource="attributes",
        action="update",
        description="Update an attribute's name, input type, unit, or status.",
    ),
]
