from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.wallets.controller import WalletController


def get_wallet_controller(db: AsyncSession = Depends(get_db)) -> WalletController:
    return WalletController(db)
