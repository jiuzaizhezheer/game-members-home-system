from uuid import UUID

from pydantic import Field

from app.database.mongodb import BaseEntity


class Notification(BaseEntity):
    user_id: UUID = Field(..., description="接收者 ID")
    type: str = Field(..., description="类型 (如 order_status, post_like, message)")
    title: str = Field(..., description="通知标题")
    body: str = Field(..., description="通知正文")
    link: str | None = Field(None, description="跳转链接")
    category: str = Field(
        default="system", description="分类: system, business, social"
    )
    is_read: bool = Field(default=False, description="是否已读")

    class Settings:
        name = "notifications"
        indexes = [
            [("user_id", 1), ("category", 1), ("is_read", 1)],
            [("user_id", 1), ("created_at", -1)],
        ]
