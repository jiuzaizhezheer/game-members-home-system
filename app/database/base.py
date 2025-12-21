from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# 基础模型类，所有模型都应继承自它
class Base(DeclarativeBase):
    pass


# 时间戳Mixin，用于添加created_at和updated_at字段
class TimestampMixin:
    """
    通用时间戳 Mixin，提供 created_at 和 updated_at 字段。
    继承此 Mixin 的模型将自动拥有这两个字段。
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="创建时间",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间",
    )
