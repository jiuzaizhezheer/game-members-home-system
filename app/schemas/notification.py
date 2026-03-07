import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SystemNotificationOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    type: str = Field(description="通知类型 (system, order, social)")
    title: str = Field(description="通知标题")
    content: str = Field(description="通知内容")
    link: str | None = Field(default=None, description="相关跳转链接")
    is_read: bool = Field(description="是否已读")
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListOut(BaseModel):
    items: list[SystemNotificationOut] = Field(description="消息列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页")
    page_size: int = Field(description="每页数量")


class UnreadCountOut(BaseModel):
    count: int = Field(description="未读消息数量")


class CreateNotificationIn(BaseModel):
    user_id: uuid.UUID
    type: str
    title: str
    content: str
    link: str | None = None
