"""Central permission registry.

Mirrors app/db/models.py's role: the one place that aggregates every
module's definitions so a single script (app/scripts/sync_permissions.py)
can reconcile them into the database.

Each module owns its permissions in its own `permissions.py` (a list of
PermissionDefinition — see app/shared/permissions.py); add one import
here for each, the same way app/db/models.py grows.
"""

from app.modules.auth.permissions import AUTH_PERMISSIONS
from app.modules.categories.permissions import CATEGORY_PERMISSIONS
from app.modules.premium.permissions import PREMIUM_PERMISSIONS
from app.modules.products.permissions import PRODUCT_PERMISSIONS
from app.modules.revenue.permissions import REVENUE_PERMISSIONS
from app.modules.sellers.permissions import SELLER_PERMISSIONS
from app.shared.permissions import PermissionDefinition

ALL_PERMISSIONS: list[PermissionDefinition] = [
    *AUTH_PERMISSIONS,
    *CATEGORY_PERMISSIONS,
    *PREMIUM_PERMISSIONS,
    *PRODUCT_PERMISSIONS,
    *REVENUE_PERMISSIONS,
    *SELLER_PERMISSIONS,
]
