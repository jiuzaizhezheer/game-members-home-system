import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

import uuid6
from sqlalchemy import (
    CheckConstraint,
    Numeric,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.pgsql import BaseEntity

if TYPE_CHECKING:
    from .orders import Order


class OrderRefund(BaseEntity):
    __tablename__ = "order_refunds"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid6.uuid7,
        comment="售后退款单ID",
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, comment="关联订单ID"
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, comment="申请用户ID"
    )
    reason: Mapped[str] = mapped_column(String(255), nullable=False, comment="退款原因")
    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, comment="退款金额"
    )
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        server_default=text("'pending'"),
        comment="退款状态",
    )
    merchant_reply: Mapped[str | None] = mapped_column(
        String(255), comment="商家审批回复"
    )

    order: Mapped["Order"] = relationship(
        "Order",
        primaryjoin="OrderRefund.order_id == Order.id",
        foreign_keys="OrderRefund.order_id",
        lazy="selectin",
        viewonly=True,
    )

    __table_args__ = (
        CheckConstraint("amount >= 0", name="chk_order_refunds_amount_nonneg"),
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')",
            name="chk_order_refunds_status",
        ),
        {"comment": "订单退款售后表"},
    )
