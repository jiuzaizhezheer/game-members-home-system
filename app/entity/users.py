import uuid

from sqlalchemy import Boolean, CheckConstraint, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        comment="用户ID",
    )
    username: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, comment="用户名"
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, comment="邮箱"
    )
    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="密码哈希"
    )
    role: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'member'"), comment="角色"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true"), comment="是否激活"
    )
    __table_args__ = (
        CheckConstraint("role IN ('member','merchant','admin')", name="chk_users_role"),
        {"comment": "用户表：平台用户基本信息与状态"},
    )

    def __repr__(self) -> str:
        return f"User(id={self.id}, username={self.username}, role={self.role}, email={self.email}, active={self.is_active})"
