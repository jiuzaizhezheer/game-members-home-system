import uuid
from decimal import Decimal

from sqlalchemy import Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.pgsql import BaseEntity


class PointLog(BaseEntity):
    __tablename__ = "point_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        comment="日志ID",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="用户ID",
    )
    change_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="变动积分数量",
    )
    balance_after: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="变动后余额",
    )
    reason: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="变动原因",
    )
    related_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="关联业务ID (如订单ID)",
    )

    def __repr__(self) -> str:
        return f"PointLog(id={self.id}, user_id={self.user_id}, change={self.change_amount}, balance={self.balance_after}, reason={self.reason})"
