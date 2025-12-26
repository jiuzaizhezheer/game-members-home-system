import uuid

from sqlalchemy import ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class Category(Base, TimestampMixin):
    __tablename__ = "categories"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        comment="分类ID",
    )
    name: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, comment="分类名称"
    )
    slug: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, comment="分类别名"
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        comment="父分类ID",
    )
    __table_args__ = (
        Index("idx_categories_parent", "parent_id"),
        {"comment": "分类表：商品分类层级与标识"},
    )

    def __repr__(self) -> str:
        return f"Category(id={self.id}, name={self.name}, parent_id={self.parent_id})"
