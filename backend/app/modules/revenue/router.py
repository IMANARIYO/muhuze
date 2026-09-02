import uuid

from fastapi import APIRouter, Depends

from app.modules.auth.dependencies import require_role
from app.modules.auth.models import Account
from app.modules.revenue.controller import RevenueController
from app.modules.revenue.dependencies import get_revenue_controller
from app.modules.revenue.schemas import (
    RevenueLine,
    RevenueSummaryResponse,
    RevenueTransactionResponse,
)
from app.modules.sellers.dependencies import get_current_seller
from app.modules.sellers.models import Seller
from app.shared.responses.helpers import success_response
from app.shared.responses.schemas import APIResponse

router = APIRouter(prefix="/revenue", tags=["Revenue"])


@router.get("/order/{order_id}/me")
async def my_order_breakdown(
    order_id: uuid.UUID,
    seller: Seller = Depends(get_current_seller),
    controller: RevenueController = Depends(get_revenue_controller),
) -> APIResponse[list[RevenueLine]]:
    """The caller's earning split for a single paid order (seller)."""
    lines = await controller.seller_order_breakdown(order_id, seller.id)
    return success_response(data=lines, message="Revenue breakdown retrieved")


@router.get("/order/{order_id}")
async def order_breakdown(
    order_id: uuid.UUID,
    account: Account = Depends(require_role("admin")),
    controller: RevenueController = Depends(get_revenue_controller),
) -> APIResponse[list[RevenueLine]]:
    """The per-seller commission split for a paid order (admin)."""
    lines = await controller.order_breakdown(order_id)
    return success_response(data=lines, message="Revenue breakdown retrieved")


@router.get("/order/{order_id}/summary")
async def order_summary(
    order_id: uuid.UUID,
    account: Account = Depends(require_role("admin")),
    controller: RevenueController = Depends(get_revenue_controller),
) -> APIResponse[RevenueSummaryResponse]:
    """Rolled-up gross, MUHUZE commission and seller net for an order (admin)."""
    summary = await controller.order_summary(order_id)
    return success_response(data=summary, message="Revenue summary retrieved")


@router.get("/me")
async def my_breakdown(
    seller: Seller = Depends(get_current_seller),
    controller: RevenueController = Depends(get_revenue_controller),
) -> APIResponse[list[RevenueLine]]:
    """The caller's earning breakdown across their paid sales."""
    lines = await controller.seller_breakdown(seller.id)
    return success_response(data=lines, message="Revenue breakdown retrieved")


@router.get("")
async def list_all(
    admin: Account = Depends(require_role("admin")),
    controller: RevenueController = Depends(get_revenue_controller),
) -> APIResponse[list[RevenueTransactionResponse]]:
    """Every revenue transaction across the platform (admin)."""
    txns = await controller.list_all()
    return success_response(data=txns, message="Revenue transactions retrieved")
