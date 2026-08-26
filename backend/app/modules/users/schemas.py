import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class ProfileUpsertRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    date_of_birth: date | None = None


class ProfileResponse(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    first_name: str
    last_name: str
    date_of_birth: date | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
