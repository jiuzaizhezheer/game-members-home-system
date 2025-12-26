import uuid

from sqlalchemy import ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class Cart(Base, TimestampMixin):
    __tablename__ = "carts"
    __table_args__ = {"comment": "购物车表：用户购物车实体"}
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        comment="购物车ID",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="用户ID",
        unique=True,
    )

    def __repr__(self) -> str:
        return f"Cart(id={self.id}, user_id={self.user_id})"
