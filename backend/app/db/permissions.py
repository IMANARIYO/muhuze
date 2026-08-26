"""Central permission registry.

Mirrors app/db/models.py's role: the one place that aggregates every
module's definitions so a single script (app/scripts/sync_permissions.py)
can reconcile them into the database.

No module needs this yet — see app/modules/auth/docs/database.md's note on
the permissions catalog. When one does, give it its own `permissions.py`
(a list of PermissionDefinition — see app/shared/permissions.py) and add
one import here, the same way app/db/models.py grows.
"""

from app.shared.permissions import PermissionDefinition

ALL_PERMISSIONS: list[PermissionDefinition] = []
