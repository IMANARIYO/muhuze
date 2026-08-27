import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SellerRegistrationRequest(BaseModel):
    business_name: str = Field(
        min_length=1, max_length=150,
        description="Business or shop name (e.g. 'Jean's Electronics')"
    )
    business_description: str | None = Field(
        default=None,
        description="Optional description of what the business sells"
    )


class SellerUpdateRequest(BaseModel):
    business_name: str = Field(
        min_length=1, max_length=150,
        description="Business or shop name"
    )
    business_description: str | None = Field(
        default=None,
        description="Optional description of what the business sells"
    )


class SellerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Seller profile ID")
    account_id: uuid.UUID = Field(description="Associated account ID")
    business_name: str = Field(description="Business or shop name")
    business_description: str | None = Field(description="Business description")
    status: str = Field(
        description=(
            "Seller status: 'draft', 'pending_review', 'active', "
            "'rejected', 'suspended', or 'deactivated'"
        )
    )
    rejection_reason: str | None = Field(
        description="Reason for rejection (set when status is 'rejected')"
    )
    submitted_at: datetime | None = Field(
        description="When the seller submitted for review (UTC, null if draft)"
    )
    reviewed_at: datetime | None = Field(
        description="When the seller was last reviewed (UTC, null if never reviewed)"
    )
    created_at: datetime = Field(description="When the seller profile was created (UTC)")
    updated_at: datetime = Field(description="When the seller profile was last updated (UTC)")


class SellerDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Document ID")
    seller_id: uuid.UUID = Field(description="Seller this document belongs to")
    document_type: str = Field(
        description=(
            "Document type: 'national_id_front', 'national_id_back', "
            "'passport', or 'driving_license'"
        )
    )
    original_filename: str | None = Field(description="Original filename when uploaded")
    mime_type: str = Field(description="MIME type of the file (e.g. 'image/jpeg')")
    file_size: int = Field(description="File size in bytes")
    url: str = Field(description="Short-lived signed URL to view the document")
    created_at: datetime = Field(description="When the document was uploaded (UTC)")


class RejectSellerRequest(BaseModel):
    reason: str = Field(
        min_length=1,
        description="Admin reason for rejecting this seller application"
    )


class SuspendSellerRequest(BaseModel):
    reason: str | None = Field(
        default=None,
        description="Optional reason for suspending this seller"
    )
