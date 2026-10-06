"""Permissions owned by the wallets feature.

There is deliberately NO permission to change a balance: balances move only
as a consequence of payments and orders (README §13.5).
"""

from app.core.permissions import PermissionDefinition

WALLET_READ_OWN = PermissionDefinition(
    code="wallet.read_own",
    name="View own wallet",
    description="See what MUHUZE owes your shop, and every movement behind it.",
    # Sellers get it automatically. It only ever reaches the caller's own wallet.
    default_roles=("seller",),
)
WALLET_READ = PermissionDefinition(
    code="wallet.read",
    name="View seller wallets",
    description="See any seller's wallet balances and movements.",
)
REVENUE_READ = PermissionDefinition(
    code="revenue.read",
    name="View revenue",
    description="See the revenue record of every sale, and MUHUZE's commission income.",
)

WALLET_PERMISSIONS = (WALLET_READ_OWN, WALLET_READ, REVENUE_READ)
