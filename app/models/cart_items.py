import uuid

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class CartItem(Base, TimestampMixin):
    __tablename__ = "cart_items"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    cart_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("carts.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_cart_items_quantity_pos"),
        CheckConstraint("unit_price >= 0", name="chk_cart_items_unit_price_nonneg"),
        UniqueConstraint("cart_id", "product_id", name="uq_cart_items_cart_product"),
        Index("idx_cart_items_cart", "cart_id"),
    )

    def __repr__(self) -> str:
        return f"CartItem(id={self.id}, cart_id={self.cart_id}, product_id={self.product_id}, qty={self.quantity})"
