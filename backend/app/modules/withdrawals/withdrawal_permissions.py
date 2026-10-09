"""Permissions owned by the withdrawals feature.

Requesting a payout touches only the caller's own money, so it has a
default role. Reviewing decides where MUHUZE's money goes and gets none
(README §5.4).
"""

from app.core.permissions import PermissionDefinition

WITHDRAWAL_REQUEST = PermissionDefinition(
    code="withdrawal.request",
    name="Request withdrawals",
    description=(
        "See and cancel your own withdrawal requests, ask for a new one, "
        "and manage your shop's payout destinations."
    ),
    default_roles=("seller",),
)
WITHDRAWAL_REVIEW = PermissionDefinition(
    code="withdrawal.review",
    name="Review withdrawals",
    description=(
        "See every withdrawal, and approve, reject, complete, or fail one after paying out by hand."
    ),
)

PAYOUT_DESTINATION_MANAGE = PermissionDefinition(
    code="payout_destination.manage",
    name="Manage payout destinations",
    description="Add, change, activate, and deactivate where your shop receives withdrawals.",
    default_roles=("seller",),
)

WITHDRAWAL_PERMISSIONS = (WITHDRAWAL_REQUEST, WITHDRAWAL_REVIEW, PAYOUT_DESTINATION_MANAGE)
