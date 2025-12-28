import uuid

from sqlalchemy import ForeignKey, Index, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class Comment(Base, TimestampMixin):
    __tablename__ = "comments"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        comment="评论ID",
    )
    post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
        comment="帖子ID",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="用户ID",
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="评论内容")
    __table_args__ = (
        Index("idx_comments_post", "post_id", "created_at"),
        {"comment": "评论表：帖子或商品的评论内容"},
    )

    def __repr__(self) -> str:
        return f"Comment(id={self.id}, post_id={self.post_id}, user_id={self.user_id})"
