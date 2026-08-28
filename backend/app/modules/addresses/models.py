import uuid

from sqlalchemy import Boolean, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDPKMixin


class ShippingAddress(UUIDPKMixin, TimestampMixin, Base):
    """One delivery destination the customer has saved (the address *book*).

    Deliberately **mutable and editable** — a customer may change their home
    address at any time. For this reason an order must **never** read its
    delivery destination directly off this table: at checkout the chosen row
    is copied into an immutable `shipping_infos` snapshot owned by the order,
    so later edits here never change past orders (see orders module).

    `recipient_name` / `phone` are who to hand the parcel to — often someone
    other than the account owner (deliver to mother, call her), so they are
    captured on the address and **not** read from `accounts`.
    """

    __tablename__ = "shipping_addresses"

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id"),
        nullable=False,
        index=True,
    )
    label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    recipient_name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    country: Mapped[str] = mapped_column(String(60), nullable=False, default="Rwanda")
    province: Mapped[str | None] = mapped_column(String(100), nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sector: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cell: Mapped[str | None] = mapped_column(String(100), nullable=True)
    village: Mapped[str | None] = mapped_column(String(100), nullable=True)
    address_line: Mapped[str | None] = mapped_column(String(255), nullable=True)
    delivery_instructions: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    def __repr__(self) -> str:
        return f"<ShippingAddress account={self.account_id} label={self.label!r}>"
