import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.pgsql import BaseEntity


class SystemNotification(BaseEntity):
    """
    系统通知实体
    用于记录发给用户的系统消息（订单动态、互动消息、系统公告等）
    """

    __tablename__ = "system_notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )  # system, order, social, etc.
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    link: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )  # 跳转链接/路由
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    # 关联 User (可选)
    user = relationship("User", backref="notifications")
