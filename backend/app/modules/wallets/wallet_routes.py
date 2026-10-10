import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.modules.auth.auth_model import Account
from app.modules.authorization.authorization_dependencies import require_permission
from app.modules.wallets.wallet_dependencies import get_own_seller_id, get_wallet_service
from app.modules.wallets.wallet_permissions import REVENUE_READ, WALLET_READ
from app.modules.wallets.wallet_schema import (
    RevenueFilters,
    RevenueSummaryResponse,
    RevenueTransactionResponse,
    WalletResponse,
    WalletTransactionResponse,
)
from app.modules.wallets.wallet_service import WalletService
from app.shared.responses.api_response import APIResponse, success_response
from app.shared.responses.pagination import Page, PaginationParams

# Read-only on purpose. Balances move only as a consequence of payments and
# orders; no endpoint can set or add to one (README §13.5).
wallet_router = APIRouter()

ServiceDep = Annotated[WalletService, Depends(get_wallet_service)]
PaginationDep = Annotated[PaginationParams, Depends()]
OwnSellerIdDep = Annotated[uuid.UUID, Depends(get_own_seller_id)]
WalletReaderDep = Annotated[Account, Depends(require_permission(WALLET_READ))]
RevenueReaderDep = Annotated[Account, Depends(require_permission(REVENUE_READ))]

WALLETS = ["Wallets"]
REVENUE = ["Revenue"]


# ── The seller's own wallet ──────────────────────────────────────────────


@wallet_router.get("/wallet/mine", response_model=APIResponse[WalletResponse], tags=WALLETS)
async def get_my_wallet(seller_id: OwnSellerIdDep, service: ServiceDep) -> JSONResponse:
    """What MUHUZE owes your shop: pending (waiting for buyers to confirm
    receipt) and available (can be withdrawn)."""
    return success_response(data=await service.get_wallet(seller_id), message="Wallet retrieved")


@wallet_router.get(
    "/wallet/mine/transactions",
    response_model=APIResponse[Page[WalletTransactionResponse]],
    tags=WALLETS,
)
async def list_my_wallet_transactions(
    seller_id: OwnSellerIdDep, pagination: PaginationDep, service: ServiceDep
) -> JSONResponse:
    """Every movement in your wallet, newest first."""
    page = await service.list_transactions(seller_id, pagination)
    return success_response(data=page, message="Transactions retrieved")


# ── Staff ────────────────────────────────────────────────────────────────


@wallet_router.get("/wallets/{seller_id}", response_model=APIResponse[WalletResponse], tags=WALLETS)
async def get_seller_wallet(
    _: WalletReaderDep, seller_id: uuid.UUID, service: ServiceDep
) -> JSONResponse:
    """Any seller's balances."""
    return success_response(data=await service.get_wallet(seller_id), message="Wallet retrieved")


@wallet_router.get(
    "/wallets/{seller_id}/transactions",
    response_model=APIResponse[Page[WalletTransactionResponse]],
    tags=WALLETS,
)
async def list_seller_wallet_transactions(
    _: WalletReaderDep, seller_id: uuid.UUID, pagination: PaginationDep, service: ServiceDep
) -> JSONResponse:
    page = await service.list_transactions(seller_id, pagination)
    return success_response(data=page, message="Transactions retrieved")


@wallet_router.get(
    "/revenue/summary", response_model=APIResponse[RevenueSummaryResponse], tags=REVENUE
)
async def get_revenue_summary(
    _: RevenueReaderDep, filters: Annotated[RevenueFilters, Depends()], service: ServiceDep
) -> JSONResponse:
    """Totals over every sale that was not reversed: what buyers paid, MUHUZE's
    commission, and what sellers earned. Optionally for one seller."""
    return success_response(
        data=await service.summarize_revenue(filters), message="Revenue summary retrieved"
    )


@wallet_router.get(
    "/revenue", response_model=APIResponse[Page[RevenueTransactionResponse]], tags=REVENUE
)
async def list_revenue(
    _: RevenueReaderDep,
    pagination: PaginationDep,
    filters: Annotated[RevenueFilters, Depends()],
    service: ServiceDep,
) -> JSONResponse:
    """The revenue record of each sale, newest first. Filter by seller or order."""
    return success_response(
        data=await service.list_revenue(pagination, filters), message="Revenue retrieved"
    )
