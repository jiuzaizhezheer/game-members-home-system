import uuid

import uuid6
from sqlalchemy import Index, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class Message(Base, TimestampMixin):
    __tablename__ = "messages"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid6.uuid7,
        comment="消息ID",
    )
    sender_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        # ForeignKey("users.id", ondelete="CASCADE"),  # 逻辑外键
        nullable=False,
        comment="发送者用户ID",
    )
    receiver_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        # ForeignKey("users.id", ondelete="CASCADE"),  # 逻辑外键
        nullable=False,
        comment="接收者用户ID",
    )
    order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        # ForeignKey("orders.id", ondelete="SET NULL"),  # 逻辑外键
        comment="关联订单ID",
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="消息内容")
    __table_args__ = (
        Index("idx_messages_pair", "sender_user_id", "receiver_user_id", "created_at"),
        {"comment": "消息表：用户私信与订单关联"},
    )

    def __repr__(self) -> str:
        return f"Message(id={self.id}, sender={self.sender_user_id}, receiver={self.receiver_user_id})"
