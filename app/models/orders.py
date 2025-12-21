import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
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
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    address_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("addresses.id", ondelete="SET NULL")
    )
    order_no: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'pending'")
    )
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    paid_at: Mapped["datetime | None"] = mapped_column(DateTime(timezone=True))
    shipped_at: Mapped["datetime | None"] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped["datetime | None"] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="chk_orders_total_amount_nonneg"),
        CheckConstraint(
            "status IN ('pending','paid','shipped','completed','cancelled')",
            name="chk_orders_status",
        ),
        Index("idx_orders_user_created", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"Order(id={self.id}, order_no={self.order_no}, user_id={self.user_id}, status={self.status}, total={self.total_amount})"
