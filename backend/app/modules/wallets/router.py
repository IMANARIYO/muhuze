import uuid

from fastapi import APIRouter, Depends, status

from app.modules.auth.dependencies import require_role
from app.modules.auth.models import Account
from app.modules.sellers.dependencies import get_current_seller
from app.modules.sellers.models import Seller
from app.modules.wallets.controller import WalletController
from app.modules.wallets.dependencies import get_wallet_controller
from app.modules.wallets.schemas import (
    AdminWalletOverviewResponse,
    CreateWithdrawalRequest,
    UpdateWithdrawalRequest,
    WalletSummaryResponse,
    WithdrawalResponse,
)
from app.shared.responses.helpers import success_response
from app.shared.responses.schemas import APIResponse

router = APIRouter(prefix="/wallet", tags=["Wallets"])


@router.get("")
async def my_wallet(
    seller: Seller = Depends(get_current_seller),
    controller: WalletController = Depends(get_wallet_controller),
) -> APIResponse[WalletSummaryResponse]:
    """The caller's seller wallet: balances, ledger history and withdrawals."""
    data = await controller.my_summary(seller.id)
    return success_response(data=data, message="Wallet retrieved")


@router.post("/withdrawals", status_code=status.HTTP_201_CREATED)
async def request_withdrawal(
    payload: CreateWithdrawalRequest,
    seller: Seller = Depends(get_current_seller),
    controller: WalletController = Depends(get_wallet_controller),
) -> APIResponse[WithdrawalResponse]:
    """Request to move available balance out to your own mobile-money number."""
    data = await controller.request_withdrawal(seller.id, payload)
    return success_response(data=data, message="Withdrawal requested")


@router.get("/admin/overview")
async def admin_overview(
    admin: Account = Depends(require_role("admin")),
    controller: WalletController = Depends(get_wallet_controller),
) -> APIResponse[AdminWalletOverviewResponse]:
    """Platform-wide wallet picture and withdrawal queue (admin)."""
    data = await controller.admin_overview()
    return success_response(data=data, message="Wallet overview retrieved")


@router.get("/admin/withdrawals")
async def list_pending_withdrawals(
    admin: Account = Depends(require_role("admin")),
    controller: WalletController = Depends(get_wallet_controller),
) -> APIResponse[list[WithdrawalResponse]]:
    """Every withdrawal awaiting admin action (admin)."""
    data = await controller.list_pending_withdrawals()
    return success_response(data=data, message="Withdrawals retrieved")


@router.post("/admin/withdrawals/{withdrawal_id}")
async def update_withdrawal(
    withdrawal_id: uuid.UUID,
    payload: UpdateWithdrawalRequest,
    admin: Account = Depends(require_role("admin")),
    controller: WalletController = Depends(get_wallet_controller),
) -> APIResponse[WithdrawalResponse]:
    """Drive a withdrawal through processing → completed (debits the wallet and
    records the payout) or cancel it (admin)."""
    data = await controller.update_withdrawal(
        withdrawal_id, admin_account_id=admin.id, payload=payload
    )
    return success_response(data=data, message="Withdrawal updated")
