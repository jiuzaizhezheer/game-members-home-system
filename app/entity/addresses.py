import uuid

from sqlalchemy import Boolean, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class Address(Base, TimestampMixin):
    __tablename__ = "addresses"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        comment="地址ID",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="用户ID",
    )
    receiver_name: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="收件人姓名"
    )
    phone: Mapped[str] = mapped_column(String(32), nullable=False, comment="联系电话")
    province: Mapped[str] = mapped_column(String(64), nullable=False, comment="省份")
    city: Mapped[str] = mapped_column(String(64), nullable=False, comment="城市")
    district: Mapped[str | None] = mapped_column(String(64), comment="区县")
    detail: Mapped[str] = mapped_column(String(255), nullable=False, comment="详细地址")
    is_default: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false"), comment="是否默认地址"
    )
    __table_args__ = (
        Index("idx_addresses_user", "user_id"),
        {"comment": "地址表：用户收货地址"},
    )

    def __repr__(self) -> str:
        return (
            f"Address(id={self.id}, user_id={self.user_id}, default={self.is_default})"
        )
