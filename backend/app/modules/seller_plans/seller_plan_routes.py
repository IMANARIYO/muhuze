import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.modules.auth.auth_model import Account
from app.modules.authorization.authorization_dependencies import require_permission
from app.modules.seller_plans.seller_plan_constants import PlanStatus
from app.modules.seller_plans.seller_plan_dependencies import get_seller_plan_service
from app.modules.seller_plans.seller_plan_permissions import (
    DEFAULT_COMMISSION_RATE_MANAGE,
    SELLER_PLAN_MANAGE,
    SELLER_SUBSCRIPTION_MANAGE,
    SELLER_SUBSCRIPTION_REQUEST,
)
from app.modules.seller_plans.seller_plan_schema import (
    CommercialTermsResponse,
    DefaultCommissionRateRequest,
    DefaultCommissionRateResponse,
    ReasonRequest,
    SellerPlanCreateRequest,
    SellerPlanResponse,
    SellerPlanUpdateRequest,
    SellerSubscriptionResponse,
    StaffPlanFilters,
    StaffSubscriptionFilters,
    SubscriptionActivateRequest,
    SubscriptionAssignRequest,
    SubscriptionRequest,
)
from app.modules.seller_plans.seller_plan_service import SellerPlanService
from app.modules.sellers.seller_dependencies import get_current_active_seller
from app.modules.sellers.seller_model import Seller
from app.shared.responses.api_response import APIResponse, success_response
from app.shared.responses.pagination import Page, PaginationParams

seller_plan_router = APIRouter()

ServiceDep = Annotated[SellerPlanService, Depends(get_seller_plan_service)]
PaginationDep = Annotated[PaginationParams, Depends()]
PlanManagerDep = Annotated[Account, Depends(require_permission(SELLER_PLAN_MANAGE))]
SubscriptionManagerDep = Annotated[Account, Depends(require_permission(SELLER_SUBSCRIPTION_MANAGE))]
RateManagerDep = Annotated[Account, Depends(require_permission(DEFAULT_COMMISSION_RATE_MANAGE))]
# A seller acting on their own subscriptions: the permission, then an active
# seller. Ownership is checked in the service.
CanRequestDep = Annotated[Account, Depends(require_permission(SELLER_SUBSCRIPTION_REQUEST))]
ActiveSellerDep = Annotated[Seller, Depends(get_current_active_seller)]

PLANS = ["Seller plans"]
SUBSCRIPTIONS = ["Seller subscriptions"]
RATES = ["Commission"]

# Fixed paths ("/manage", "/mine") are declared before "/{id}" paths so they
# are never read as an id.

# ── Plans ────────────────────────────────────────────────────────────────


@seller_plan_router.get(
    "/seller-plans", response_model=APIResponse[Page[SellerPlanResponse]], tags=PLANS
)
async def list_offered_plans(pagination: PaginationDep, service: ServiceDep) -> JSONResponse:
    """The plans on offer, cheapest first. Public."""
    return success_response(
        data=await service.list_offered_plans(pagination), message="Plans retrieved"
    )


@seller_plan_router.get(
    "/seller-plans/manage", response_model=APIResponse[Page[SellerPlanResponse]], tags=PLANS
)
async def list_all_plans(
    _: PlanManagerDep,
    pagination: PaginationDep,
    filters: Annotated[StaffPlanFilters, Depends()],
    service: ServiceDep,
) -> JSONResponse:
    """Every plan, including retired ones."""
    return success_response(
        data=await service.list_all_plans(pagination, filters), message="Plans retrieved"
    )


@seller_plan_router.post(
    "/seller-plans",
    response_model=APIResponse[SellerPlanResponse],
    status_code=status.HTTP_201_CREATED,
    tags=PLANS,
)
async def create_plan(
    admin: PlanManagerDep, payload: SellerPlanCreateRequest, service: ServiceDep
) -> JSONResponse:
    """Add a plan to the catalogue."""
    plan = await service.create_plan(payload=payload, created_by=admin.id)
    return success_response(
        data=SellerPlanResponse.model_validate(plan),
        message="Plan created",
        status_code=status.HTTP_201_CREATED,
    )


@seller_plan_router.patch(
    "/seller-plans/{plan_id}", response_model=APIResponse[SellerPlanResponse], tags=PLANS
)
async def update_plan(
    admin: PlanManagerDep,
    plan_id: uuid.UUID,
    payload: SellerPlanUpdateRequest,
    service: ServiceDep,
) -> JSONResponse:
    """Change a plan. Sellers already subscribed keep the terms they started with."""
    plan = await service.update_plan(plan_id, payload=payload, updated_by=admin.id)
    return success_response(data=SellerPlanResponse.model_validate(plan), message="Plan updated")


@seller_plan_router.post(
    "/seller-plans/{plan_id}/retire", response_model=APIResponse[SellerPlanResponse], tags=PLANS
)
async def retire_plan(
    admin: PlanManagerDep, plan_id: uuid.UUID, service: ServiceDep
) -> JSONResponse:
    """Stop offering a plan. Existing subscriptions to it run their course."""
    plan = await service.set_plan_status(plan_id, PlanStatus.RETIRED, changed_by=admin.id)
    return success_response(data=SellerPlanResponse.model_validate(plan), message="Plan retired")


@seller_plan_router.post(
    "/seller-plans/{plan_id}/reactivate",
    response_model=APIResponse[SellerPlanResponse],
    tags=PLANS,
)
async def reactivate_plan(
    admin: PlanManagerDep, plan_id: uuid.UUID, service: ServiceDep
) -> JSONResponse:
    """Offer a retired plan again."""
    plan = await service.set_plan_status(plan_id, PlanStatus.ACTIVE, changed_by=admin.id)
    return success_response(
        data=SellerPlanResponse.model_validate(plan), message="Plan offered again"
    )


@seller_plan_router.delete("/seller-plans/{plan_id}", response_model=APIResponse[None], tags=PLANS)
async def delete_plan(
    admin: PlanManagerDep, plan_id: uuid.UUID, service: ServiceDep
) -> JSONResponse:
    """Delete a plan nobody ever subscribed to. Retire any other."""
    await service.delete_plan(plan_id, deleted_by=admin.id)
    return success_response(message="Plan deleted")


# ── A seller's own subscriptions ─────────────────────────────────────────


@seller_plan_router.get(
    "/seller-subscriptions/mine/terms",
    response_model=APIResponse[CommercialTermsResponse],
    tags=SUBSCRIPTIONS,
)
async def get_my_terms(
    _: CanRequestDep, seller: ActiveSellerDep, service: ServiceDep
) -> JSONResponse:
    """The commission you are charged right now, the plan behind it, what is
    scheduled next, and any request still waiting."""
    return success_response(data=await service.get_own_terms(seller.id), message="Terms retrieved")


@seller_plan_router.get(
    "/seller-subscriptions/mine",
    response_model=APIResponse[Page[SellerSubscriptionResponse]],
    tags=SUBSCRIPTIONS,
)
async def list_my_subscriptions(
    _: CanRequestDep, seller: ActiveSellerDep, pagination: PaginationDep, service: ServiceDep
) -> JSONResponse:
    """Your subscription history, newest first."""
    page = await service.list_own_subscriptions(seller_id=seller.id, pagination=pagination)
    return success_response(data=page, message="Subscriptions retrieved")


@seller_plan_router.post(
    "/seller-subscriptions/mine",
    response_model=APIResponse[SellerSubscriptionResponse],
    status_code=status.HTTP_201_CREATED,
    tags=SUBSCRIPTIONS,
)
async def request_plan(
    account: CanRequestDep,
    seller: ActiveSellerDep,
    payload: SubscriptionRequest,
    service: ServiceDep,
) -> JSONResponse:
    """Ask for a plan. It starts once MUHUZE has confirmed your payment."""
    subscription = await service.request_plan(
        seller_id=seller.id, plan_id=payload.plan_id, requested_by=account.id
    )
    return success_response(
        data=subscription,
        message="Plan requested. It starts once your payment is confirmed.",
        status_code=status.HTTP_201_CREATED,
    )


@seller_plan_router.post(
    "/seller-subscriptions/mine/{subscription_id}/withdraw",
    response_model=APIResponse[SellerSubscriptionResponse],
    tags=SUBSCRIPTIONS,
)
async def withdraw_my_request(
    account: CanRequestDep,
    seller: ActiveSellerDep,
    subscription_id: uuid.UUID,
    service: ServiceDep,
) -> JSONResponse:
    """Take back a request that is still waiting."""
    subscription = await service.withdraw_request(
        seller_id=seller.id, subscription_id=subscription_id, withdrawn_by=account.id
    )
    return success_response(data=subscription, message="Request withdrawn")


# ── Staff: subscriptions ─────────────────────────────────────────────────


@seller_plan_router.get(
    "/seller-subscriptions",
    response_model=APIResponse[Page[SellerSubscriptionResponse]],
    tags=SUBSCRIPTIONS,
)
async def list_all_subscriptions(
    _: SubscriptionManagerDep,
    pagination: PaginationDep,
    filters: Annotated[StaffSubscriptionFilters, Depends()],
    service: ServiceDep,
) -> JSONResponse:
    """Every seller's subscriptions. Use `status=pending` for the requests
    waiting for a decision."""
    page = await service.list_all_subscriptions(pagination, filters)
    return success_response(data=page, message="Subscriptions retrieved")


@seller_plan_router.post(
    "/seller-subscriptions",
    response_model=APIResponse[SellerSubscriptionResponse],
    status_code=status.HTTP_201_CREATED,
    tags=SUBSCRIPTIONS,
)
async def assign_plan(
    admin: SubscriptionManagerDep, payload: SubscriptionAssignRequest, service: ServiceDep
) -> JSONResponse:
    """Give a plan to a seller directly. It is active at once."""
    subscription = await service.assign(payload=payload, assigned_by=admin.id)
    return success_response(
        data=subscription, message="Plan assigned", status_code=status.HTTP_201_CREATED
    )


@seller_plan_router.post(
    "/seller-subscriptions/{subscription_id}/activate",
    response_model=APIResponse[SellerSubscriptionResponse],
    tags=SUBSCRIPTIONS,
)
async def activate_subscription(
    admin: SubscriptionManagerDep,
    subscription_id: uuid.UUID,
    payload: SubscriptionActivateRequest,
    service: ServiceDep,
) -> JSONResponse:
    """Activate a pending request after checking the seller's payment."""
    subscription = await service.activate(
        subscription_id=subscription_id,
        payment_reference=payload.payment_reference,
        activated_by=admin.id,
    )
    return success_response(data=subscription, message="Subscription activated")


@seller_plan_router.post(
    "/seller-subscriptions/{subscription_id}/reject",
    response_model=APIResponse[SellerSubscriptionResponse],
    tags=SUBSCRIPTIONS,
)
async def reject_subscription(
    admin: SubscriptionManagerDep,
    subscription_id: uuid.UUID,
    payload: ReasonRequest,
    service: ServiceDep,
) -> JSONResponse:
    """Decline a pending request, with a reason the seller sees."""
    subscription = await service.reject(
        subscription_id=subscription_id, reason=payload.reason, rejected_by=admin.id
    )
    return success_response(data=subscription, message="Request rejected")


@seller_plan_router.post(
    "/seller-subscriptions/{subscription_id}/cancel",
    response_model=APIResponse[SellerSubscriptionResponse],
    tags=SUBSCRIPTIONS,
)
async def cancel_subscription(
    admin: SubscriptionManagerDep,
    subscription_id: uuid.UUID,
    payload: ReasonRequest,
    service: ServiceDep,
) -> JSONResponse:
    """End a running or scheduled subscription early, with a reason."""
    subscription = await service.cancel(
        subscription_id=subscription_id, reason=payload.reason, cancelled_by=admin.id
    )
    return success_response(data=subscription, message="Subscription cancelled")


# ── Staff: default commission rate ───────────────────────────────────────


@seller_plan_router.get(
    "/commission-rates/default",
    response_model=APIResponse[DefaultCommissionRateResponse],
    tags=RATES,
)
async def get_default_rate(_: RateManagerDep, service: ServiceDep) -> JSONResponse:
    """The commission rate in force for sellers without a plan."""
    return success_response(data=await service.get_default_rate(), message="Rate retrieved")


@seller_plan_router.get(
    "/commission-rates/default/history",
    response_model=APIResponse[Page[DefaultCommissionRateResponse]],
    tags=RATES,
)
async def list_default_rates(
    _: RateManagerDep, pagination: PaginationDep, service: ServiceDep
) -> JSONResponse:
    """Every default rate ever set, newest first: who, when, and why."""
    return success_response(
        data=await service.list_default_rates(pagination), message="Rates retrieved"
    )


@seller_plan_router.post(
    "/commission-rates/default",
    response_model=APIResponse[DefaultCommissionRateResponse],
    status_code=status.HTTP_201_CREATED,
    tags=RATES,
)
async def set_default_rate(
    admin: RateManagerDep, payload: DefaultCommissionRateRequest, service: ServiceDep
) -> JSONResponse:
    """Set the rate for sellers without a plan, from now or from a future
    moment. Orders already created keep the rate they recorded."""
    rate = await service.set_default_rate(payload=payload, set_by=admin.id)
    return success_response(
        data=rate, message="Default commission rate set", status_code=status.HTTP_201_CREATED
    )
