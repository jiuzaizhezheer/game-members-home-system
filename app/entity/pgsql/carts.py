import uuid

import uuid6
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.pgsql import BaseEntity


class Cart(BaseEntity):
    __tablename__ = "carts"
    __table_args__ = {"comment": "购物车表：用户购物车实体"}
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid6.uuid7,
        comment="购物车ID",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        # ForeignKey("users.id", ondelete="CASCADE"),  # 逻辑外键
        nullable=False,
        comment="用户ID",
    )
    name: Mapped[str] = mapped_column(
        default="默认购物车",
        comment="购物车名称",
    )
    is_checked_out: Mapped[bool] = mapped_column(
        default=False,
        comment="是否已结算/过期",
    )

    def __repr__(self) -> str:
        return f"Cart(id={self.id}, user_id={self.user_id})"
