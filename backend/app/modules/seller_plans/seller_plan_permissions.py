"""Permissions owned by the seller plans feature.

The three staff permissions change what MUHUZE earns, so each is separate
and none has a default role: only `admin` holds them until an admin decides
otherwise (README §5.4).
"""

from app.core.permissions import PermissionDefinition

SELLER_PLAN_MANAGE = PermissionDefinition(
    code="seller_plan.manage",
    name="Manage seller plans",
    description="Create, change, and retire the plans offered to sellers, and see retired ones.",
)
SELLER_SUBSCRIPTION_MANAGE = PermissionDefinition(
    code="seller_subscription.manage",
    name="Manage seller subscriptions",
    description=(
        "See every seller's subscriptions, activate or reject requests, assign a plan "
        "to a seller, and end a subscription early."
    ),
)
DEFAULT_COMMISSION_RATE_MANAGE = PermissionDefinition(
    code="default_commission_rate.manage",
    name="Manage the default commission rate",
    description="See and change the commission rate applied to sellers without a plan.",
)
SELLER_SUBSCRIPTION_REQUEST = PermissionDefinition(
    code="seller_subscription.request",
    name="Request a plan",
    description="Request a plan for your own shop and see your own subscriptions.",
    # Sellers get it automatically. It only ever reaches the caller's own
    # subscriptions, and the seller must also be active.
    default_roles=("seller",),
)

SELLER_PLAN_PERMISSIONS = (
    SELLER_PLAN_MANAGE,
    SELLER_SUBSCRIPTION_MANAGE,
    DEFAULT_COMMISSION_RATE_MANAGE,
    SELLER_SUBSCRIPTION_REQUEST,
)
