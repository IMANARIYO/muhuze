import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SellerUpsertRequest(BaseModel):
    store_name: str = Field(min_length=1, max_length=150)
    description: str | None = None


class SellerResponse(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    store_name: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
