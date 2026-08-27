import uuid
from enum import StrEnum

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDPKMixin


class CategoryStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Category(UUIDPKMixin, TimestampMixin, Base):
    """Hierarchical product classification for browsing/filtering — not
    ownership. A Product belongs to exactly one Category; Category nests
    arbitrarily deep via parent_id (self-referential), e.g. Electronics >
    Phones > Smartphones. Duplicate names are prevented under the same
    parent (same name under different parents is allowed)."""

    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint(
            "parent_id",
            "name",
            name="uq_categories_parent_name",
        ),
    )

    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(170), unique=True, nullable=False, index=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=CategoryStatus.ACTIVE, index=True
    )
