import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

import uuid6

if TYPE_CHECKING:
    from .products import Product
from sqlalchemy import (
    CheckConstraint,
    Index,
    Integer,
    Numeric,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.pgsql import BaseEntity


class OrderItem(BaseEntity):
    __tablename__ = "order_items"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid6.uuid7,
        comment="明细ID",
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        # ForeignKey("orders.id", ondelete="CASCADE"),  # 逻辑外键
        nullable=False,
        comment="订单ID",
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        # ForeignKey("products.id", ondelete="RESTRICT"),  # 逻辑外键
        nullable=False,
        comment="商品ID",
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, comment="数量")

    # 关联
    product: Mapped["Product"] = relationship(
        "Product",
        primaryjoin="OrderItem.product_id == Product.id",
        foreign_keys="OrderItem.product_id",
        lazy="selectin",
        viewonly=True,
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, comment="单价"
    )
    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_order_items_quantity_pos"),
        CheckConstraint("unit_price >= 0", name="chk_order_items_unit_price_nonneg"),
        UniqueConstraint("order_id", "product_id"),
        Index("idx_order_items_order", "order_id"),
        {"comment": "订单明细表：订单中的商品项"},
    )

    def __repr__(self) -> str:
        return f"OrderItem(id={self.id}, order_id={self.order_id}, product_id={self.product_id}, qty={self.quantity})"
