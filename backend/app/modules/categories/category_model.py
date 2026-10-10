"""Persistence models for categories.

Mirrors `docs/database/database_schema.dbml`; change both together.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    false,
    text,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.modules.categories.category_constants import (
    ATTRIBUTE_CODE_MAX_LENGTH,
    ATTRIBUTE_NAME_MAX_LENGTH,
    ATTRIBUTE_UNIT_MAX_LENGTH,
    CATEGORY_DESCRIPTION_MAX_LENGTH,
    CATEGORY_NAME_MAX_LENGTH,
    CATEGORY_SLUG_MAX_LENGTH,
    OPTION_VALUE_MAX_LENGTH,
    AttributeDataType,
)


class Category(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A section of ONE seller's shop. There is no shared marketplace tree:
    another seller's "Phones" is a different row (README §7.2)."""

    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("seller_id", "slug"),
        # Names are unique within a shop whatever the letter case.
        Index("uq_categories_seller_id_name_lower", "seller_id", text("lower(name)"), unique=True),
    )

    seller_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sellers.id", ondelete="RESTRICT"))
    name: Mapped[str] = mapped_column(String(CATEGORY_NAME_MAX_LENGTH))
    slug: Mapped[str] = mapped_column(String(CATEGORY_SLUG_MAX_LENGTH))
    description: Mapped[str | None] = mapped_column(String(CATEGORY_DESCRIPTION_MAX_LENGTH))
    sort_order: Mapped[int] = mapped_column(default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(default=True, server_default=true())
    # Set when staff hide the category; the seller cannot reactivate it.
    hidden_by_staff_at: Mapped[datetime | None]


class CategoryAttribute(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """What a product in the category is described by: Storage, Colour, …"""

    __tablename__ = "category_attributes"
    __table_args__ = (
        UniqueConstraint("category_id", "code"),
        CheckConstraint(
            f"data_type IN ({', '.join(repr(t.value) for t in AttributeDataType)})",
            name="data_type_valid",
        ),
    )

    category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"))
    # Stable key for the API and product data. Made from the first name and
    # never changed, so renaming the label doesn't orphan product values.
    code: Mapped[str] = mapped_column(String(ATTRIBUTE_CODE_MAX_LENGTH))
    name: Mapped[str] = mapped_column(String(ATTRIBUTE_NAME_MAX_LENGTH))
    data_type: Mapped[str] = mapped_column(String(20))
    unit: Mapped[str | None] = mapped_column(String(ATTRIBUTE_UNIT_MAX_LENGTH))
    is_required: Mapped[bool] = mapped_column(default=False, server_default=false())
    is_filterable: Mapped[bool] = mapped_column(default=False, server_default=false())
    sort_order: Mapped[int] = mapped_column(default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(default=True, server_default=true())


class CategoryAttributeOption(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One allowed value of a select / multi_select attribute."""

    __tablename__ = "category_attribute_options"
    __table_args__ = (
        Index(
            "uq_category_attribute_options_attribute_id_value_lower",
            "attribute_id",
            text("lower(value)"),
            unique=True,
        ),
    )

    attribute_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("category_attributes.id", ondelete="CASCADE")
    )
    value: Mapped[str] = mapped_column(String(OPTION_VALUE_MAX_LENGTH))
    sort_order: Mapped[int] = mapped_column(default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(default=True, server_default=true())
