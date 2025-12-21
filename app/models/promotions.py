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


class Promotion(Base, TimestampMixin):
    __tablename__ = "promotions"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    discount_type: Mapped[str] = mapped_column(String(16), nullable=False)
    discount_value: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'active'")
    )
    __table_args__ = (
        CheckConstraint("discount_value >= 0", name="chk_promotions_value_nonneg"),
        CheckConstraint(
            "discount_type IN ('percent','fixed')", name="chk_promotions_type"
        ),
        CheckConstraint(
            "status IN ('active','inactive')", name="chk_promotions_status"
        ),
        Index("idx_promotions_merchant", "merchant_id"),
        Index("idx_promotions_period", "start_at", "end_at"),
    )

    def __repr__(self) -> str:
        return f"Promotion(id={self.id}, title={self.title}, merchant_id={self.merchant_id}, status={self.status})"
