import uuid
from datetime import datetime

import uuid6
from sqlalchemy import CheckConstraint, DateTime, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.pgsql import BaseEntity


class Payment(BaseEntity):
    __tablename__ = "payments"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid6.uuid7,
        comment="支付ID",
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        # ForeignKey("orders.id", ondelete="CASCADE"),  # 逻辑外键
        nullable=False,
        comment="订单ID",
        unique=True,
    )
    method: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'online'"), comment="支付方式"
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'unpaid'"), comment="支付状态"
    )
    amount: Mapped[float] = mapped_column(
        Numeric(12, 2), nullable=False, comment="支付金额"
    )
    transaction_no: Mapped[str | None] = mapped_column(String(64), comment="交易流水号")
    paid_at: Mapped["datetime | None"] = mapped_column(
        DateTime(timezone=True), comment="支付时间"
    )
    __table_args__ = (
        CheckConstraint("amount >= 0", name="chk_payments_amount_nonneg"),
        CheckConstraint("method IN ('online','cod')", name="chk_payments_method"),
        CheckConstraint(
            "status IN ('unpaid','success','failed','refunded')",
            name="chk_payments_status",
        ),
        {"comment": "支付表：订单支付记录与状态"},
    )

    def __repr__(self) -> str:
        return f"Payment(id={self.id}, order_id={self.order_id}, status={self.status}, amount={self.amount})"
