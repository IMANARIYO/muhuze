import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.wallets.wallet_constants import WalletTransactionKind


class WalletResponse(BaseModel):
    """What MUHUZE owes a seller. Not money the seller already has: that
    only happens through a withdrawal."""

    seller_id: uuid.UUID
    currency: str
    pending_balance: Decimal = Field(
        description="Earned, waiting for the buyer to confirm receipt; cannot be withdrawn"
    )
    available_balance: Decimal = Field(description="Can be withdrawn")
    total_earned: Decimal = Field(description="Everything ever earned, less what was reversed")
    total_withdrawn: Decimal


class WalletTransactionResponse(BaseModel):
    id: uuid.UUID
    kind: WalletTransactionKind
    pending_change: Decimal = Field(description="Signed")
    available_change: Decimal = Field(description="Signed")
    pending_after: Decimal
    available_after: Decimal
    order_id: uuid.UUID = Field(description="The order the movement comes from")
    seller_order_id: uuid.UUID
    created_at: datetime


class RevenueTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    seller_order_id: uuid.UUID
    order_id: uuid.UUID
    seller_id: uuid.UUID
    gross_amount: Decimal = Field(description="What the buyer paid for this shop's part")
    commission_rate: Decimal
    commission_amount: Decimal = Field(description="MUHUZE's income from the sale")
    seller_amount: Decimal = Field(description="What MUHUZE owes the seller for the sale")
    currency: str
    reversed_at: datetime | None = Field(description="Set if the sale was undone")
    created_at: datetime


class RevenueSummaryResponse(BaseModel):
    """Totals over sales that were not reversed."""

    sales: int = Field(description="Number of seller orders")
    gross_amount: Decimal = Field(description="What buyers paid")
    commission_amount: Decimal = Field(description="MUHUZE's commission income")
    seller_amount: Decimal = Field(description="What sellers earned")
    currency: str


class RevenueFilters(BaseModel):
    seller_id: uuid.UUID | None = None
    order_id: uuid.UUID | None = None
