import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CategoryCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150, description="Category name")
    description: str | None = Field(default=None, description="Optional category description")
    parent_id: uuid.UUID | None = Field(
        default=None,
        description="Parent category ID. Null for top-level categories."
    )
    sort_order: int = Field(default=0, description="Display sort order (0-based)")


class CategoryUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150, description="Category name")
    description: str | None = Field(default=None, description="Optional category description")
    sort_order: int = Field(default=0, description="Display sort order (0-based)")
    status: str = Field(description="Category status: 'active' or 'inactive'")


class CategoryMoveRequest(BaseModel):
    parent_id: uuid.UUID | None = Field(
        description=(
            "New parent category ID. Null to move to top-level. "
            "Cannot be the category itself or one of its descendants."
        )
    )


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Category ID")
    parent_id: uuid.UUID | None = Field(description="Parent category ID (null for top-level)")
    name: str = Field(description="Category name")
    slug: str = Field(description="URL-safe slug (auto-generated from name)")
    description: str | None = Field(description="Category description")
    image: str | None = Field(description="Cloudinary URL for category image")
    sort_order: int = Field(description="Display sort order (0-based)")
    status: str = Field(description="Category status: 'active' or 'inactive'")
    created_at: datetime = Field(description="When the category was created (UTC)")
    updated_at: datetime = Field(description="When the category was last updated (UTC)")
