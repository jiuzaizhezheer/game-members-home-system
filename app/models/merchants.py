import uuid

from sqlalchemy import ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class Merchant(Base, TimestampMixin):
    __tablename__ = "merchants"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    shop_name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    contact_phone: Mapped[str | None] = mapped_column(String(32))
    shop_desc: Mapped[str | None] = mapped_column(Text)

    def __repr__(self) -> str:
        return f"Merchant(id={self.id}, shop_name={self.shop_name}, user_id={self.user_id})"
