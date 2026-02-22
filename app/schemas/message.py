"""消息相关的请求和响应模型"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class MessageSendIn(BaseModel):
    """发送消息请求"""

    receiver_user_id: uuid.UUID = Field(description="接收者用户 ID")
    content: str = Field(min_length=1, max_length=2000, description="消息内容")
    content_type: str = Field(default="text", description="消息类型: text, image")
    order_id: uuid.UUID | None = Field(None, description="关联订单 ID")


class MessageItemOut(BaseModel):
    """单条消息响应"""

    id: str
    sender_id: str
    content: str
    content_type: str = "text"
    is_mine: bool = Field(description="是否是自己发的")
    created_at: datetime


class ConversationItemOut(BaseModel):
    """会话列表项"""

    partner_user_id: str = Field(description="对方用户 ID")
    partner_name: str = Field(description="对方用户名")
    last_message: str = Field(description="最后一条消息内容")
    last_message_type: str = Field(default="text", description="最后一条消息类型")
    last_message_at: datetime = Field(description="最后一条消息时间")
    unread_count: int = Field(default=0, description="未读消息数")
    avatar_url: str | None = Field(default=None, description="对方头像地址")


class ConversationListOut(BaseModel):
    """会话列表响应"""

    items: list[ConversationItemOut]


class MessageListOut(BaseModel):
    """消息列表响应"""

    items: list[MessageItemOut]
    has_more: bool = False
