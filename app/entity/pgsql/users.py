import uuid

import uuid6
from sqlalchemy import Boolean, CheckConstraint, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.pgsql import BaseEntity


class User(BaseEntity):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid6.uuid7,
        comment="用户ID",
    )
    username: Mapped[str] = mapped_column(String(64), nullable=False, comment="用户名")
    email: Mapped[str] = mapped_column(String(255), nullable=False, comment="邮箱")
    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="密码哈希"
    )
    role: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'member'"), comment="角色"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true"), comment="是否激活"
    )
    avatar_url: Mapped[str | None] = mapped_column(
        String(512), nullable=True, comment="头像地址"
    )
    __table_args__ = (
        CheckConstraint("role IN ('member','merchant','admin')", name="chk_users_role"),
        UniqueConstraint("username", "role", name="uq_users_username_role"),
        UniqueConstraint("email", "role", name="uq_users_email_role"),
        {"comment": "用户表：平台用户基本信息与状态"},
    )

    def __repr__(self) -> str:
        return f"User(id={self.id}, username={self.username}, role={self.role}, email={self.email}, active={self.is_active})"
