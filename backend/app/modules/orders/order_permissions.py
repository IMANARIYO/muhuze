"""Permissions owned by the orders feature.

Placing an order and managing your own orders need no permission, only a
login: every account can buy (README §6.2), and those endpoints only ever
reach the caller's own orders.
"""

from app.core.permissions import PermissionDefinition

SELLER_ORDER_MANAGE = PermissionDefinition(
    code="seller_order.manage",
    name="Handle own shop orders",
    description="See the paid orders of your own shop and accept, reject, ship, and deliver them.",
    # Sellers get it automatically. It only ever reaches the caller's own
    # shop's orders, and the seller must also be active.
    default_roles=("seller",),
)
ORDER_READ = PermissionDefinition(
    code="order.read",
    name="View all orders",
    description=(
        "See every order of every buyer and shop, including each shop's commission and earnings."
    ),
)

ORDER_PERMISSIONS = (SELLER_ORDER_MANAGE, ORDER_READ)
