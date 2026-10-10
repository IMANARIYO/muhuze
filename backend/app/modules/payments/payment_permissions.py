"""Permissions owned by the payments feature.

Both decide where money goes or whether it is considered received, so each
is separate and neither has a default role (README §5.4, §12.10).
Paying for your own order needs no permission, only a login.
"""

from app.core.permissions import PermissionDefinition

PAYMENT_DESTINATION_MANAGE = PermissionDefinition(
    code="payment_destination.manage",
    name="Manage payment destinations",
    description=(
        "See, add, change, activate, and deactivate the accounts MUHUZE receives buyers' money on."
    ),
)
PAYMENT_VERIFY = PermissionDefinition(
    code="payment.verify",
    name="Verify payments",
    description=(
        "See every payment, and approve or reject one after checking it against "
        "MUHUZE's account statement. Approving releases the order to its sellers."
    ),
)

PAYMENT_PERMISSIONS = (PAYMENT_DESTINATION_MANAGE, PAYMENT_VERIFY)
