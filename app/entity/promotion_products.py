import uuid

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class PromotionProduct(Base, TimestampMixin):
    __tablename__ = "promotion_products"
    __table_args__ = {"comment": "促销商品关联表：活动与商品的多对多关系"}
    promotion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        # ForeignKey("promotions.id", ondelete="CASCADE"),  # 逻辑外键
        primary_key=True,
        comment="促销ID",
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        # ForeignKey("products.id", ondelete="CASCADE"),  # 逻辑外键
        primary_key=True,
        comment="商品ID",
    )

    def __repr__(self) -> str:
        return f"PromotionProduct(promotion_id={self.promotion_id}, product_id={self.product_id})"
