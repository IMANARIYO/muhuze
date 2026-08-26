import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SellerRegistrationRequest(BaseModel):
    business_name: str = Field(min_length=1, max_length=150)
    business_description: str | None = None


class SellerUpdateRequest(BaseModel):
    business_name: str = Field(min_length=1, max_length=150)
    business_description: str | None = None


class SellerResponse(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    business_name: str
    business_description: str | None
    status: str
    rejection_reason: str | None
    submitted_at: datetime | None
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SellerDocumentResponse(BaseModel):
    id: uuid.UUID
    seller_id: uuid.UUID
    document_type: str
    original_filename: str | None
    mime_type: str
    file_size: int
    url: str
    created_at: datetime


class RejectSellerRequest(BaseModel):
    reason: str = Field(min_length=1)


class SuspendSellerRequest(BaseModel):
    reason: str | None = None
