import uuid

from fastapi import APIRouter, Depends, status

from app.modules.auth.dependencies import require_role
from app.modules.auth.models import Account
from app.modules.premium.controller import PremiumController
from app.modules.premium.dependencies import get_premium_controller
from app.modules.premium.schemas import (
    PremiumPlanRequest,
    PremiumPlanResponse,
    PremiumPlanUpdateRequest,
    SellerSubscriptionResponse,
    SubscribeRequest,
    SubscriptionStatusResponse,
)
from app.modules.sellers.dependencies import get_current_seller
from app.modules.sellers.models import Seller
from app.shared.responses.helpers import success_response
from app.shared.responses.schemas import APIResponse

router = APIRouter(prefix="/premium", tags=["Premium"])


# ── plans (public read, admin write) ──────────────────────────────────


@router.get("/plans")
async def list_plans(
    controller: PremiumController = Depends(get_premium_controller),
) -> APIResponse[list[PremiumPlanResponse]]:
    """List the premium plans currently available to buy. Public — the
    seller-facing 'subscribe' page renders this. Each plan carries its
    `commission_rate` (the % of each sale MUHUZE keeps while on it)."""
    plans = await controller.list_available_plans()
    return success_response(data=plans, message="Premium plans retrieved successfully")


@router.post("/plans", status_code=status.HTTP_201_CREATED)
async def create_plan(
    payload: PremiumPlanRequest,
    admin: Account = Depends(require_role("admin")),
    controller: PremiumController = Depends(get_premium_controller),
) -> APIResponse[PremiumPlanResponse]:
    """Create a new premium plan (admin). This is where the rates are set —
    `commission_rate` decides how much MUHUZE keeps from a subscribed
    seller's sales."""
    plan = await controller.create_plan(payload)
    return success_response(data=plan, message="Premium plan created successfully")


@router.patch("/plans/{plan_id}")
async def update_plan(
    plan_id: uuid.UUID,
    payload: PremiumPlanUpdateRequest,
    admin: Account = Depends(require_role("admin")),
    controller: PremiumController = Depends(get_premium_controller),
) -> APIResponse[PremiumPlanResponse]:
    """Update a premium plan (admin) — e.g. change `commission_rate`, price,
    duration, or `is_active`. Changing the rate affects *future*
    subscriptions only; existing sellers keep their purchase-time snapshot."""
    plan = await controller.update_plan(plan_id, payload)
    return success_response(data=plan, message="Premium plan updated successfully")


# ── seller self-service ───────────────────────────────────────────────


@router.get("/me")
async def my_status(
    seller: Seller = Depends(get_current_seller),
    controller: PremiumController = Depends(get_premium_controller),
) -> APIResponse[SubscriptionStatusResponse]:
    """The caller's subscription status: whether they're premium, the
    current subscription (if any), and the commission rate that applies to
    their sales right now (7% premium / 12% basic)."""
    status_data = await controller.my_status(seller)
    return success_response(data=status_data, message="Subscription status retrieved")


@router.post("/subscribe", status_code=status.HTTP_201_CREATED)
async def subscribe(
    payload: SubscribeRequest,
    seller: Seller = Depends(get_current_seller),
    controller: PremiumController = Depends(get_premium_controller),
) -> APIResponse[SellerSubscriptionResponse]:
    """Subscribe the caller's seller account to a plan. Buying a new plan
    replaces (marks expired) any current active subscription so only one is
    live at a time. The plan's commission rate is snapshotted on this row."""
    subscription = await controller.subscribe(seller, payload)
    return success_response(
        data=subscription, message="Subscription created successfully"
    )


@router.get("/me/subscription")
async def my_subscription(
    seller: Seller = Depends(get_current_seller),
    controller: PremiumController = Depends(get_premium_controller),
) -> APIResponse[SellerSubscriptionResponse]:
    """The caller's current active subscription (404 if they're a basic,
    non-subscribed seller)."""
    subscription = await controller.my_subscription(seller)
    return success_response(
        data=subscription, message="Active subscription retrieved successfully"
    )


@router.post("/me/cancel")
async def cancel(
    seller: Seller = Depends(get_current_seller),
    controller: PremiumController = Depends(get_premium_controller),
) -> APIResponse[SellerSubscriptionResponse]:
    """Cancel the caller's active subscription. The seller immediately drops
    back to the basic 12% commission rate."""
    subscription = await controller.cancel(seller)
    return success_response(data=subscription, message="Subscription cancelled")


@router.get("/me/history")
async def my_history(
    seller: Seller = Depends(get_current_seller),
    controller: PremiumController = Depends(get_premium_controller),
) -> APIResponse[list[SellerSubscriptionResponse]]:
    """The caller's full subscription purchase history, newest first."""
    history = await controller.my_history(seller)
    return success_response(
        data=history, message="Subscription history retrieved successfully"
    )


# ── admin ─────────────────────────────────────────────────────────────


@router.get("/subscriptions")
async def list_subscriptions(
    admin: Account = Depends(require_role("admin")),
    controller: PremiumController = Depends(get_premium_controller),
) -> APIResponse[list[SellerSubscriptionResponse]]:
    """List every seller subscription across the platform (admin)."""
    subscriptions = await controller.list_all_subscriptions()
    return success_response(
        data=subscriptions, message="Subscriptions retrieved successfully"
    )
