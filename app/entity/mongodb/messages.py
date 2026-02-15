from uuid import UUID

from pydantic import BaseModel, Field

from app.database.mongodb import BaseEntity


class MessageContent(BaseModel):
    type: str = Field(..., description="消息类型: text, image, file, order_card")
    body: str = Field(..., description="消息内容正文或链接")


class Message(BaseEntity):
    conversation_id: str = Field(..., description="会话ID (由两个用户ID排序后拼接)")
    sender_id: UUID = Field(..., description="发送者用户 ID")
    receiver_id: UUID = Field(..., description="接收者用户 ID")
    order_id: UUID | None = Field(None, description="关联的订单 ID (可选)")
    content: MessageContent = Field(..., description="消息内容对象")
    is_read: bool = Field(default=False, description="已读状态")
    deleted_by: list[UUID] = Field(
        default_factory=list, description="存储已删除此消息的用户 ID"
    )

    class Settings:
        name = "messages"
        indexes = [
            [("conversation_id", 1), ("created_at", -1)],
            [("receiver_id", 1), ("is_read", 1)],
        ]
