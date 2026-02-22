import uuid

import uuid6
from sqlalchemy import Boolean, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.pgsql import BaseEntity


class Post(BaseEntity):
    __tablename__ = "posts"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid6.uuid7,
        comment="帖子ID",
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        # ForeignKey("community_groups.id", ondelete="CASCADE"),  # 逻辑外键
        nullable=False,
        comment="社群ID",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        # ForeignKey("users.id", ondelete="CASCADE"),  # 逻辑外键
        nullable=False,
        comment="用户ID",
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, comment="标题")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="内容")
    images: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        default=[],
        nullable=False,
        server_default=text("'{}'"),
        comment="图片列表",
    )
    videos: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        default=[],
        nullable=False,
        server_default=text("'{}'"),
        comment="视频列表",
    )
    view_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, server_default=text("0"), comment="浏览数"
    )
    likes_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, server_default=text("0"), comment="点赞数"
    )
    comment_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, server_default=text("0"), comment="评论数"
    )
    is_top: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        server_default=text("false"),
        comment="是否置顶",
    )
    is_hidden: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        server_default=text("false"),
        comment="是否隐藏",
    )
    __table_args__ = (
        Index("idx_posts_group", "group_id", "created_at"),
        Index("idx_posts_user", "user_id", "created_at"),
        {"comment": "帖子表：社区帖子与互动数据"},
    )

    def __repr__(self) -> str:
        return f"Post(id={self.id}, title={self.title}, user_id={self.user_id})"
