import uuid
from decimal import Decimal

import uuid6
from sqlalchemy import (
    CheckConstraint,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.pgsql import BaseEntity


class Product(BaseEntity):
    __tablename__ = "products"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid6.uuid7,
        comment="商品ID",
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        # ForeignKey("merchants.id", ondelete="CASCADE"),  # 逻辑外键
        nullable=False,
        comment="商家ID",
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="商品名称")
    sku: Mapped[str | None] = mapped_column(String(64), unique=True, comment="商品SKU")
    description: Mapped[str | None] = mapped_column(Text, comment="商品描述")
    price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, comment="商品价格"
    )
    stock: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"), comment="库存数量"
    )
    status: Mapped[str] = mapped_column(
        String(8), nullable=False, server_default=text("'on'"), comment="上下架状态"
    )
    popularity_score: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"), comment="热度评分"
    )
    views_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"), comment="浏览次数"
    )
    sales_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"), comment="销售数量"
    )
    image_url: Mapped[str | None] = mapped_column(String(512), comment="商品图片URL")
    __table_args__ = (
        CheckConstraint("price >= 0", name="chk_products_price_nonneg"),
        CheckConstraint("stock >= 0", name="chk_products_stock_nonneg"),
        CheckConstraint("status IN ('on','off')", name="chk_products_status"),
        Index("idx_products_merchant", "merchant_id"),
        Index(
            "idx_products_popularity",
            "popularity_score",
            "sales_count",
            postgresql_using="btree",
        ),
        Index("idx_products_views", "views_count", postgresql_using="btree"),
        Index("idx_products_name", "name", postgresql_using="btree"),
        {"comment": "商品表：保存商品基本信息与统计数据"},
    )

    def __repr__(self) -> str:
        return f"Product(id={self.id}, name={self.name}, status={self.status})"
