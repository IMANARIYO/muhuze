import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.wallets.schemas import (
    AdminWalletOverviewResponse,
    CreateWithdrawalRequest,
    UpdateWithdrawalRequest,
    WalletSummaryResponse,
    WithdrawalResponse,
)
from app.modules.wallets.service import WalletService


class WalletController:
    """Translates HTTP requests/responses to and from the wallet service."""

    def __init__(self, db: AsyncSession) -> None:
        self.service = WalletService(db)

    async def my_summary(self, seller_id: uuid.UUID) -> WalletSummaryResponse:
        data = await self.service.get_summary(seller_id)
        return WalletSummaryResponse.model_validate(
            {
                "wallet": data["wallet"],
                "transactions": data["transactions"],
                "withdrawals": data["withdrawals"],
            }
        )

    async def request_withdrawal(
        self, seller_id: uuid.UUID, payload: CreateWithdrawalRequest
    ) -> WithdrawalResponse:
        withdrawal = await self.service.request_withdrawal(
            seller_id,
            amount=payload.amount,
            mobile_money_number=payload.mobile_money_number,
            note=payload.note,
        )
        return WithdrawalResponse.model_validate(withdrawal)

    async def admin_overview(self) -> AdminWalletOverviewResponse:
        data = await self.service.get_admin_overview()
        return AdminWalletOverviewResponse.model_validate(data)

    async def list_pending_withdrawals(self) -> list[WithdrawalResponse]:
        rows = await self.service.list_pending_withdrawals()
        return [WithdrawalResponse.model_validate(w) for w in rows]

    async def update_withdrawal(
        self,
        withdrawal_id: uuid.UUID,
        admin_account_id: uuid.UUID,
        payload: UpdateWithdrawalRequest,
    ) -> WithdrawalResponse:
        withdrawal = await self.service.update_withdrawal(
            withdrawal_id,
            status=payload.status,
            admin_account_id=admin_account_id,
            note=payload.note,
        )
        return WithdrawalResponse.model_validate(withdrawal)
