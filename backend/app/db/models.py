"""Central model registry.

Import every module's models here so `Base.metadata` is fully populated for
Alembic autogenerate. Add one import per new model — nothing else needs to
change (not env.py, not this file's structure).
"""

from app.modules.auth.models import (  # noqa: F401
    Account,
    AccountPermission,
    AccountRole,
    PasswordResetToken,
    Permission,
    RefreshToken,
    Role,
    RolePermission,
    VerificationCode,
)
from app.modules.sellers.models import Seller, SellerDocument  # noqa: F401
from app.modules.users.models import Profile  # noqa: F401
