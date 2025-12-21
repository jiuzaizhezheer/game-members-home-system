import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    method: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'online'")
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'unpaid'")
    )
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    transaction_no: Mapped[str | None] = mapped_column(String(64))
    paid_at: Mapped["datetime | None"] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        CheckConstraint("amount >= 0", name="chk_payments_amount_nonneg"),
        CheckConstraint("method IN ('online','cod')", name="chk_payments_method"),
        CheckConstraint(
            "status IN ('unpaid','success','failed','refunded')",
            name="chk_payments_status",
        ),
    )

    def __repr__(self) -> str:
        return f"Payment(id={self.id}, order_id={self.order_id}, status={self.status}, amount={self.amount})"
