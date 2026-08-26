from fastapi import APIRouter, Depends

from app.modules.auth.dependencies import get_current_account
from app.modules.auth.models import Account
from app.modules.sellers.controller import SellerController
from app.modules.sellers.dependencies import get_seller_controller
from app.modules.sellers.schemas import SellerUpsertRequest
from app.shared.responses.helpers import success_response
from app.shared.responses.schemas import APIResponse

router = APIRouter(prefix="/sellers", tags=["Sellers"])


@router.get("/me")
async def get_my_seller(
    account: Account = Depends(get_current_account),
    controller: SellerController = Depends(get_seller_controller),
) -> APIResponse:
    seller = await controller.get_my_seller(account.id)
    return success_response(
        data=seller, message="Seller profile retrieved successfully"
    )


@router.put("/me")
async def upsert_my_seller(
    payload: SellerUpsertRequest,
    account: Account = Depends(get_current_account),
    controller: SellerController = Depends(get_seller_controller),
) -> APIResponse:
    seller = await controller.upsert_my_seller(account.id, payload)
    return success_response(data=seller, message="Seller profile saved successfully")
