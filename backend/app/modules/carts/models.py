import uuid

from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDPKMixin


class CartItem(UUIDPKMixin, TimestampMixin, Base):
    """One line in a buyer's cart: a specific seller's offer, at a specific
    quantity.

    The cart references `seller_listings` (a *specific seller's offer at a
    specific price*) rather than just the product variant — because the
    customer buys a seller's listing, not the variant in the abstract. This
    is exactly what `order_items` later snapshots at checkout, so the cart
    and the order agree on which seller fulfills which line.

    A cart is implicit (rows keyed by account) — there is no separate `cart`
    table in v1. Rows are per (account, listing): adding the same listing
    again bumps `quantity` instead of inserting a duplicate row.
    """

    __tablename__ = "cart_items"
    __table_args__ = (
        UniqueConstraint(
            "account_id", "listing_id", name="uq_cart_items_account_listing"
        ),
    )

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id"),
        nullable=False,
        index=True,
    )
    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("seller_listings.id"),
        nullable=False,
        index=True,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    def __repr__(self) -> str:
        return f"<CartItem account={self.account_id} listing={self.listing_id} qty={self.quantity}>"
