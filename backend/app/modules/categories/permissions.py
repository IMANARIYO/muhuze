"""Category permissions.

Maps the admin-only category tree management in
app/modules/categories/router.py. Aggregated into ALL_PERMISSIONS in
app/db/permissions.py.
"""

from app.shared.permissions import PermissionDefinition

CATEGORY_PERMISSIONS = [
    PermissionDefinition(
        code="categories.create",
        name="Create categories",
        resource="categories",
        action="create",
        description="Create a category or subcategory in the tree.",
    ),
    PermissionDefinition(
        code="categories.update",
        name="Update categories",
        resource="categories",
        action="update",
        description="Update a category's name, description, or status.",
    ),
    PermissionDefinition(
        code="categories.move",
        name="Move categories",
        resource="categories",
        action="move",
        description="Reparent a category within the tree.",
    ),
]
