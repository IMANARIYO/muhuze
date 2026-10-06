"""The complete permission catalog: every feature's permissions in one tuple.

Add a feature's `<FEATURE>_PERMISSIONS` here when it gets its
`<feature>_permissions.py`. The catalog is synced into the database at
startup (app/bootstrap.py).
"""

from app.core.permissions import PermissionDefinition
from app.modules.authorization.authorization_permissions import AUTHORIZATION_PERMISSIONS
from app.modules.categories.category_permissions import CATEGORY_PERMISSIONS
from app.modules.sellers.seller_permissions import SELLER_PERMISSIONS

ALL_PERMISSIONS: tuple[PermissionDefinition, ...] = (
    *AUTHORIZATION_PERMISSIONS,
    *SELLER_PERMISSIONS,
    *CATEGORY_PERMISSIONS,
)

_codes = [permission.code for permission in ALL_PERMISSIONS]
if len(_codes) != len(set(_codes)):
    raise RuntimeError("Duplicate permission codes in the permission catalog")
