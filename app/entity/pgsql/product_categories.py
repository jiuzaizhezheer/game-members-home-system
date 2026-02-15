import uuid

from sqlalchemy import Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.pgsql import BaseEntity


class ProductCategory(BaseEntity):
    __tablename__ = "product_categories"
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        # ForeignKey("products.id", ondelete="CASCADE"),  # 逻辑外键
        primary_key=True,
        comment="商品ID",
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        # ForeignKey("categories.id", ondelete="CASCADE"),  # 逻辑外键
        primary_key=True,
        comment="分类ID",
    )
    __table_args__ = (
        Index("idx_product_categories_category", "category_id"),
        {"comment": "商品分类关联表：商品与分类的多对多关系"},
    )

    def __repr__(self) -> str:
        return f"ProductCategory(product_id={self.product_id}, category_id={self.category_id})"
