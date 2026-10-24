import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.modules.auth.auth_dependencies import get_current_account
from app.modules.auth.auth_model import Account
from app.modules.authorization.authorization_dependencies import require_permission
from app.modules.orders.order_schema import OrderCancelRequest, ReasonRequest
from app.modules.sellers.seller_dependencies import get_current_active_seller
from app.modules.sellers.seller_model import Seller
from app.modules.service_requests.service_request_dependencies import (
    get_service_request_service,
)
from app.modules.service_requests.service_request_permissions import (
    SERVICE_REQUEST_MANAGE,
    SERVICE_REQUEST_READ,
)
from app.modules.service_requests.service_request_schema import (
    ServiceRequestCreateRequest,
    ServiceRequestFilters,
    ServiceRequestResponse,
    StaffServiceRequestFilters,
)
from app.modules.service_requests.service_request_service import ServiceRequestService
from app.shared.responses.api_response import APIResponse, success_response
from app.shared.responses.pagination import Page, PaginationParams

service_request_router = APIRouter(prefix="/service-requests", tags=["Service requests"])

ServiceDep = Annotated[ServiceRequestService, Depends(get_service_request_service)]
PaginationDep = Annotated[PaginationParams, Depends()]
# Every account can buy: the buyer's endpoints need a login only, and reach
# only the caller's own requests.
BuyerDep = Annotated[Account, Depends(get_current_account)]
# A provider answering their shop's requests: the permission, then an active
# seller. Ownership is checked in the service.
CanAnswerDep = Annotated[Account, Depends(require_permission(SERVICE_REQUEST_MANAGE))]
ActiveSellerDep = Annotated[Seller, Depends(get_current_active_seller)]
StaffDep = Annotated[Account, Depends(require_permission(SERVICE_REQUEST_READ))]

# Fixed paths ("/mine", "/incoming") are declared before "/{request_id}" so
# they are never read as an id.

# ── The buyer ────────────────────────────────────────────────────────────


@service_request_router.post(
    "", response_model=APIResponse[ServiceRequestResponse], status_code=status.HTTP_201_CREATED
)
async def request_service(
    buyer: BuyerDep, payload: ServiceRequestCreateRequest, service: ServiceDep
) -> JSONResponse:
    """Ask a provider for a service at a time and place. The price is read
    from the listing. You pay only once the provider accepts."""
    request = await service.create_request(buyer_account_id=buyer.id, payload=payload)
    return success_response(
        data=request,
        message="Request sent. You can pay once the provider accepts it.",
        status_code=status.HTTP_201_CREATED,
    )


@service_request_router.get("/mine", response_model=APIResponse[Page[ServiceRequestResponse]])
async def list_my_requests(
    buyer: BuyerDep,
    pagination: PaginationDep,
    filters: Annotated[ServiceRequestFilters, Depends()],
    service: ServiceDep,
) -> JSONResponse:
    """Your service requests, newest first."""
    page = await service.list_own_requests(
        buyer_account_id=buyer.id, pagination=pagination, filters=filters
    )
    return success_response(data=page, message="Service requests retrieved")


@service_request_router.get(
    "/mine/{request_id}", response_model=APIResponse[ServiceRequestResponse]
)
async def get_my_request(
    buyer: BuyerDep, request_id: uuid.UUID, service: ServiceDep
) -> JSONResponse:
    """One of your requests. Once accepted, `order` is the order to pay."""
    request = await service.get_own_request(buyer_account_id=buyer.id, request_id=request_id)
    return success_response(data=request, message="Service request retrieved")


@service_request_router.post(
    "/mine/{request_id}/cancel", response_model=APIResponse[ServiceRequestResponse]
)
async def cancel_my_request(
    buyer: BuyerDep, request_id: uuid.UUID, payload: OrderCancelRequest, service: ServiceDep
) -> JSONResponse:
    """Withdraw a request the provider has not answered yet. After it is
    accepted, cancel the unpaid order instead."""
    request = await service.cancel_own_request(
        buyer_account_id=buyer.id, request_id=request_id, reason=payload.reason
    )
    return success_response(data=request, message="Service request cancelled")


# ── The provider ─────────────────────────────────────────────────────────


@service_request_router.get("/incoming", response_model=APIResponse[Page[ServiceRequestResponse]])
async def list_incoming_requests(
    _: CanAnswerDep,
    seller: ActiveSellerDep,
    pagination: PaginationDep,
    filters: Annotated[ServiceRequestFilters, Depends()],
    service: ServiceDep,
) -> JSONResponse:
    """The requests sent to your shop, newest first."""
    page = await service.list_incoming_requests(
        seller_id=seller.id, pagination=pagination, filters=filters
    )
    return success_response(data=page, message="Service requests retrieved")


@service_request_router.get(
    "/incoming/{request_id}", response_model=APIResponse[ServiceRequestResponse]
)
async def get_incoming_request(
    _: CanAnswerDep, seller: ActiveSellerDep, request_id: uuid.UUID, service: ServiceDep
) -> JSONResponse:
    """One request sent to your shop: when, where, and whom to contact."""
    request = await service.get_incoming_request(seller_id=seller.id, request_id=request_id)
    return success_response(data=request, message="Service request retrieved")


@service_request_router.post(
    "/incoming/{request_id}/accept", response_model=APIResponse[ServiceRequestResponse]
)
async def accept_request(
    account: CanAnswerDep, seller: ActiveSellerDep, request_id: uuid.UUID, service: ServiceDep
) -> JSONResponse:
    """Agree to do it. An order is created for the buyer to pay; once it is
    paid it appears in your shop orders."""
    request = await service.accept(seller_id=seller.id, request_id=request_id, actor_id=account.id)
    return success_response(data=request, message="Request accepted. The buyer can now pay.")


@service_request_router.post(
    "/incoming/{request_id}/decline", response_model=APIResponse[ServiceRequestResponse]
)
async def decline_request(
    account: CanAnswerDep,
    seller: ActiveSellerDep,
    request_id: uuid.UUID,
    payload: ReasonRequest,
    service: ServiceDep,
) -> JSONResponse:
    """Say no, with a reason the buyer sees."""
    request = await service.decline(
        seller_id=seller.id, request_id=request_id, actor_id=account.id, reason=payload.reason
    )
    return success_response(data=request, message="Request declined")


# ── Staff ────────────────────────────────────────────────────────────────


@service_request_router.get("", response_model=APIResponse[Page[ServiceRequestResponse]])
async def list_all_requests(
    _: StaffDep,
    pagination: PaginationDep,
    filters: Annotated[StaffServiceRequestFilters, Depends()],
    service: ServiceDep,
) -> JSONResponse:
    """Every service request. Filter by status, provider, or buyer."""
    page = await service.list_all_requests(pagination, filters)
    return success_response(data=page, message="Service requests retrieved")


@service_request_router.get("/{request_id}", response_model=APIResponse[ServiceRequestResponse])
async def get_any_request(_: StaffDep, request_id: uuid.UUID, service: ServiceDep) -> JSONResponse:
    """Any service request in full."""
    return success_response(
        data=await service.get_any_request(request_id), message="Service request retrieved"
    )
