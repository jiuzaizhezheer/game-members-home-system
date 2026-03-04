import uuid

from sqlalchemy import (
    Boolean,
    Integer,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.pgsql import BaseEntity


class Banner(BaseEntity):
    __tablename__ = "banners"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        comment="Banner ID",
    )
    title: Mapped[str] = mapped_column(String(128), nullable=False, comment="标题")
    image_url: Mapped[str] = mapped_column(
        String(512), nullable=False, comment="图片链接"
    )
    link_url: Mapped[str | None] = mapped_column(String(512), comment="跳转链接")
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0"), comment="排序权重"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true"), comment="是否启用"
    )

    __table_args__ = ({"comment": "首页轮播图管理表"},)

    def __repr__(self) -> str:
        return f"Banner(id={self.id}, title={self.title}, is_active={self.is_active})"
