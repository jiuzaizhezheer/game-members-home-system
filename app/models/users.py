import uuid

from sqlalchemy import Boolean, CheckConstraint, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'member'")
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    __table_args__ = (
        CheckConstraint("role IN ('member','merchant','admin')", name="chk_users_role"),
    )

    def __repr__(self) -> str:
        return f"User(id={self.id}, username={self.username}, role={self.role}, email={self.email}, active={self.is_active})"
