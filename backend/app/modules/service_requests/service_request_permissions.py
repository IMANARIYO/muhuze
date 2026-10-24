"""Permissions owned by the service-requests feature.

Requesting a service and managing your own requests need no permission, only
a login: every account can buy (README §6.2), and those endpoints only ever
reach the caller's own requests.
"""

from app.core.permissions import PermissionDefinition

SERVICE_REQUEST_MANAGE = PermissionDefinition(
    code="service_request.manage",
    name="Answer own service requests",
    description="See the service requests sent to your own shop, and accept or decline them.",
    # Sellers get it automatically. It only ever reaches the caller's own
    # shop's requests, and the seller must also be active.
    default_roles=("seller",),
)
SERVICE_REQUEST_READ = PermissionDefinition(
    code="service_request.read",
    name="View all service requests",
    description="See every service request of every buyer and provider.",
)

SERVICE_REQUEST_PERMISSIONS = (SERVICE_REQUEST_MANAGE, SERVICE_REQUEST_READ)
