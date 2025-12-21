import uuid

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class Product(Base, TimestampMixin):
    __tablename__ = "products"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(64), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    stock: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    status: Mapped[str] = mapped_column(
        String(8), nullable=False, server_default=text("'on'")
    )
    popularity_score: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    views_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    sales_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
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
    )

    def __repr__(self) -> str:
        return f"Product(id={self.id}, name={self.name}, status={self.status})"
