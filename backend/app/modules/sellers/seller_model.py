"""Persistence models for sellers.

Mirrors `docs/database/database_schema.dbml`; change both together.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.modules.sellers.seller_constants import (
    ADDRESS_PART_MAX_LENGTH,
    BUSINESS_NAME_MAX_LENGTH,
    DEFAULT_COUNTRY_CODE,
    IDENTITY_DOCUMENT_NUMBER_MAX_LENGTH,
    ORIGINAL_FILENAME_MAX_LENGTH,
    STATUS_REASON_MAX_LENGTH,
    STREET_ADDRESS_MAX_LENGTH,
    IdentityDocumentType,
    LocationSource,
    SellerDocumentType,
    SellerStatus,
)


def _in_values(column: str, enum: type[StrEnum]) -> str:
    return f"{column} IN ({', '.join(repr(member.value) for member in enum)})"


class Seller(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """How an account trades, and whether that is currently trusted.

    1:0..1 with Account and never merged into it. One row per account,
    forever: a rejected seller edits and resubmits the same row. Never
    deleted; the lifecycle is always a status change.
    """

    __tablename__ = "sellers"
    __table_args__ = (
        CheckConstraint(_in_values("status", SellerStatus), name="status_valid"),
        CheckConstraint(
            _in_values("identity_document_type", IdentityDocumentType),
            name="identity_document_type_valid",
        ),
        CheckConstraint(
            f"location_source IS NULL OR {_in_values('location_source', LocationSource)}",
            name="location_source_valid",
        ),
        CheckConstraint(
            "(latitude IS NULL) = (longitude IS NULL)", name="coordinates_both_or_neither"
        ),
        CheckConstraint(
            "latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180",
            name="coordinates_in_range",
        ),
        # Shop names are unique whatever the letter case.
        Index("uq_sellers_business_name_lower", text("lower(business_name)"), unique=True),
        Index("ix_sellers_status", "status"),
    )

    account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("accounts.id", ondelete="RESTRICT"), unique=True
    )

    business_name: Mapped[str] = mapped_column(String(BUSINESS_NAME_MAX_LENGTH))
    business_description: Mapped[str | None] = mapped_column(Text)
    business_phone: Mapped[str] = mapped_column(String(20))

    identity_document_type: Mapped[str] = mapped_column(String(20))
    # Sensitive: shown to the owner and to reviewing admins only, never logged.
    identity_document_number: Mapped[str] = mapped_column(
        String(IDENTITY_DOCUMENT_NUMBER_MAX_LENGTH)
    )

    country_code: Mapped[str] = mapped_column(
        String(2), default=DEFAULT_COUNTRY_CODE, server_default=DEFAULT_COUNTRY_CODE
    )
    province: Mapped[str] = mapped_column(String(ADDRESS_PART_MAX_LENGTH))
    district: Mapped[str] = mapped_column(String(ADDRESS_PART_MAX_LENGTH))
    sector: Mapped[str] = mapped_column(String(ADDRESS_PART_MAX_LENGTH))
    cell: Mapped[str | None] = mapped_column(String(ADDRESS_PART_MAX_LENGTH))
    village: Mapped[str | None] = mapped_column(String(ADDRESS_PART_MAX_LENGTH))
    street_address: Mapped[str | None] = mapped_column(String(STREET_ADDRESS_MAX_LENGTH))
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    location_accuracy_m: Mapped[int | None]
    location_source: Mapped[str | None] = mapped_column(String(20))
    location_captured_at: Mapped[datetime | None]

    status: Mapped[str] = mapped_column(
        String(20), default=SellerStatus.DRAFT.value, server_default=SellerStatus.DRAFT.value
    )
    status_reason: Mapped[str | None] = mapped_column(String(STATUS_REASON_MAX_LENGTH))
    submitted_at: Mapped[datetime | None]
    reviewed_by_account_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("accounts.id", ondelete="SET NULL")
    )
    reviewed_at: Mapped[datetime | None]
    # First approval. Never cleared, so "was approved once" survives a suspension.
    approved_at: Mapped[datetime | None]


class SellerDocument(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One uploaded file of a seller application, stored privately.

    Only what is needed to find the file is kept, never a URL: links are
    signed per request and expire (infrastructure/storage/file_storage.py).
    """

    __tablename__ = "seller_documents"
    __table_args__ = (
        UniqueConstraint("seller_id", "document_type"),
        CheckConstraint(
            _in_values("document_type", SellerDocumentType), name="document_type_valid"
        ),
    )

    seller_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sellers.id", ondelete="CASCADE"))
    document_type: Mapped[str] = mapped_column(String(30))
    storage_public_id: Mapped[str] = mapped_column(String(255))
    storage_resource_type: Mapped[str] = mapped_column(String(20))
    storage_format: Mapped[str] = mapped_column(String(10))
    original_filename: Mapped[str | None] = mapped_column(String(ORIGINAL_FILENAME_MAX_LENGTH))
    mime_type: Mapped[str] = mapped_column(String(100))
    file_size: Mapped[int]


class SellerStatusHistory(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Append-only: one row per status change. Never updated or deleted."""

    __tablename__ = "seller_status_history"

    seller_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sellers.id", ondelete="CASCADE"), index=True
    )
    from_status: Mapped[str | None] = mapped_column(String(20))
    to_status: Mapped[str] = mapped_column(String(20))
    reason: Mapped[str | None] = mapped_column(String(STATUS_REASON_MAX_LENGTH))
    changed_by_account_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("accounts.id", ondelete="SET NULL")
    )
