from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PermissionDefinition:
    """A permission as code defines it, before it's synced into the
    database. Modules that need finer-grained authorization than a role
    check declare a list of these in their own `permissions.py`; see
    app/db/permissions.py for how they're aggregated and
    app/core/permissions_sync.py for how they reach the database."""

    code: str
    name: str
    resource: str
    action: str
    description: str | None = None
