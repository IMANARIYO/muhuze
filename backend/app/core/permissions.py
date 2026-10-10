"""How a feature declares the permissions it needs.

Permissions are a fixed catalog defined in code. Each feature lists its own
in `<feature>_permissions.py`:

    PRODUCT_CREATE = PermissionDefinition(
        code="product.create",
        name="Create products",
        description="Add a new product to the seller's own shop.",
        default_roles=("seller",),
    )
    PRODUCT_PERMISSIONS = (PRODUCT_CREATE, ...)

and adds that tuple to `app/core/permission_registry.py`. At startup the
catalog is synced into the `permissions` table. Admins can assign these
permissions to roles and accounts, but can never invent new ones.
"""

import re
from dataclasses import dataclass

# <resource>.<action>, lowercase, singular resource: product.create
PERMISSION_CODE_PATTERN = re.compile(r"^[a-z][a-z_]*\.[a-z][a-z_]*$")


@dataclass(frozen=True, slots=True)
class PermissionDefinition:
    code: str
    name: str
    description: str
    # Roles that receive the permission when it is first added to the
    # database. Later changes by an admin are never overwritten. The `admin`
    # role always holds every permission and doesn't need to be listed.
    default_roles: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not PERMISSION_CODE_PATTERN.fullmatch(self.code):
            raise ValueError(
                f"Invalid permission code {self.code!r}: expected '<resource>.<action>'"
            )

    @property
    def resource(self) -> str:
        return self.code.split(".")[0]

    @property
    def action(self) -> str:
        return self.code.split(".")[1]
