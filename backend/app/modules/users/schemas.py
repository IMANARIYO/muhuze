import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ProfileUpsertRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100, description="First name")
    last_name: str = Field(min_length=1, max_length=100, description="Last name")
    date_of_birth: date | None = Field(default=None, description="Date of birth (optional)")


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Profile ID")
    account_id: uuid.UUID = Field(description="Associated account ID")
    first_name: str = Field(description="First name")
    last_name: str = Field(description="Last name")
    date_of_birth: date | None = Field(description="Date of birth (if provided)")
    created_at: datetime = Field(description="When the profile was created (UTC)")
    updated_at: datetime = Field(description="When the profile was last updated (UTC)")
