import uuid

from sqlalchemy import Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.pgsql import BaseEntity


class Favorite(BaseEntity):
    __tablename__ = "favorites"
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        # ForeignKey("users.id", ondelete="CASCADE"),  # 逻辑外键
        primary_key=True,
        comment="用户ID",
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        # ForeignKey("products.id", ondelete="CASCADE"),  # 逻辑外键
        primary_key=True,
        comment="商品ID",
    )
    __table_args__ = (
        Index("idx_favorites_user", "user_id"),
        {"comment": "收藏表：用户收藏的商品"},
    )

    def __repr__(self) -> str:
        return f"Favorite(user_id={self.user_id}, product_id={self.product_id})"
