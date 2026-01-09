import uuid

import uuid6
from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class Merchant(Base, TimestampMixin):
    __tablename__ = "merchants"
    __table_args__ = {"comment": "商家表：店铺与商家主体信息"}
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid6.uuid7,
        comment="商家ID",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        # ForeignKey("users.id", ondelete="CASCADE"),  # 逻辑外键
        nullable=False,
        comment="关联用户ID",
        unique=True,
    )
    shop_name: Mapped[str] = mapped_column(
        String(128), nullable=False, unique=True, comment="店铺名称"
    )
    contact_phone: Mapped[str | None] = mapped_column(String(32), comment="联系电话")
    shop_desc: Mapped[str | None] = mapped_column(Text, comment="店铺描述")

    def __repr__(self) -> str:
        return f"Merchant(id={self.id}, shop_name={self.shop_name}, user_id={self.user_id})"
