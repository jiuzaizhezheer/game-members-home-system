import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class GroupMember(Base, TimestampMixin):
    __tablename__ = "group_members"
    __table_args__ = {"comment": "社群成员表：用户加入小组的关系"}
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("community_groups.id", ondelete="CASCADE"),
        primary_key=True,
        comment="社群ID",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        comment="用户ID",
    )
    joined_at: Mapped["datetime"] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
        comment="加入时间",
    )

    def __repr__(self) -> str:
        return f"GroupMember(group_id={self.group_id}, user_id={self.user_id})"
