import uuid
from datetime import datetime

import uuid6
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Index,
    Numeric,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class Order(Base, TimestampMixin):
    __tablename__ = "orders"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid6.uuid7,
        comment="订单ID",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        # ForeignKey("users.id", ondelete="RESTRICT"),  # 逻辑外键
        nullable=False,
        comment="用户ID",
    )
    address_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        # ForeignKey("addresses.id", ondelete="SET NULL"),  # 逻辑外键
        comment="收货地址ID",
    )
    order_no: Mapped[str] = mapped_column(
        String(32), nullable=False, unique=True, comment="订单编号"
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'pending'"), comment="订单状态"
    )
    total_amount: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False, comment="订单总金额"
    )
    paid_at: Mapped["datetime | None"] = mapped_column(
        DateTime(timezone=True), comment="支付时间"
    )
    shipped_at: Mapped["datetime | None"] = mapped_column(
        DateTime(timezone=True), comment="发货时间"
    )
    completed_at: Mapped["datetime | None"] = mapped_column(
        DateTime(timezone=True), comment="完成时间"
    )
    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="chk_orders_total_amount_nonneg"),
        CheckConstraint(
            "status IN ('pending','paid','shipped','completed','cancelled')",
            name="chk_orders_status",
        ),
        Index("idx_orders_user_created", "user_id", "created_at"),
        Index("idx_orders_status", "status"),
        {"comment": "订单表：用户订单及其状态"},
    )

    def __repr__(self) -> str:
        return f"Order(id={self.id}, order_no={self.order_no}, user_id={self.user_id}, status={self.status}, total={self.total_amount})"
