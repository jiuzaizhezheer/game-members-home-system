import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.pgsql import BaseEntity


class OrderLogistics(BaseEntity):
    __tablename__ = "order_logistics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        comment="物流记录ID",
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        # ForeignKey("orders.id", ondelete="CASCADE"), # 采用逻辑关联节省部署成本
        nullable=False,
        comment="订单ID",
    )
    status_message: Mapped[str] = mapped_column(
        String(256), nullable=False, comment="状态描述"
    )
    location: Mapped[str | None] = mapped_column(
        String(128), comment="地理位置（城市/站点）"
    )
    log_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        comment="记录时间",
    )

    __table_args__ = ({"comment": "订单物流追踪记录表"},)

    def __repr__(self) -> str:
        return f"OrderLogistics(id={self.id}, order_id={self.order_id}, message={self.status_message})"
