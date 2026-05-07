"""消息服务层：消息业务逻辑"""

from uuid import UUID

from app.common.errors import BusinessError, NotFoundError
from app.core.websocket_manager import chat_ws_manager
from app.database.pgsql import get_pg
from app.repo import messages_repo, products_repo, users_repo
from app.schemas.message import (
    ConversationItemOut,
    ConversationListOut,
    MessageItemOut,
    MessageListOut,
    MessageSendIn,
)


class MessageService:
    """消息服务"""

    async def send_message(
        self, user_id: str, payload: MessageSendIn
    ) -> MessageItemOut:
        """发送消息"""
        receiver_id = str(payload.receiver_user_id)

        # 不能给自己发消息
        if user_id == receiver_id:
            raise BusinessError(detail="不能给自己发消息")

        # 验证接收者存在
        async with get_pg() as session:
            receiver = await users_repo.get_by_id(session, receiver_id)
            if not receiver:
                raise NotFoundError("接收者不存在")

        msg = await messages_repo.send_message(
            sender_id=UUID(user_id),
            receiver_id=payload.receiver_user_id,
            content=payload.content,
            content_type=payload.content_type,
            product_id=payload.product_id,
            order_id=payload.order_id,
        )

        await chat_ws_manager.broadcast_to_user(
            receiver_id,
            {
                "type": "NEW_MESSAGE",
                "data": {
                    "id": str(msg.id),
                    "sender_id": user_id,
                    "receiver_id": receiver_id,
                    "content": msg.content.body,
                    "content_type": msg.content.type,
                    "product_id": str(msg.product_id) if msg.product_id else None,
                    "created_at": msg.created_at.isoformat(),
                },
            },
        )

        return MessageItemOut(
            id=str(msg.id),
            sender_id=user_id,
            content=msg.content.body,
            content_type=msg.content.type,
            product_id=str(msg.product_id) if msg.product_id else None,
            is_mine=True,
            created_at=msg.created_at,
        )

    async def get_conversations(self, user_id: str) -> ConversationListOut:
        """获取会话列表"""
        raw_conversations = await messages_repo.get_conversations(user_id)

        items: list[ConversationItemOut] = []
        for conv in raw_conversations:
            # 找到对方的 user_id：最新消息中不是自己的那个就是对方
            def _to_uuid_str(val):
                if isinstance(val, bytes | bytearray):
                    return str(UUID(bytes=bytes(val)))
                # MongoDB Binary -> bytes
                if hasattr(val, "sub_type") and hasattr(val, "__bytes__"):
                    return str(UUID(bytes=bytes(val)))
                return str(val)

            sender_id = _to_uuid_str(conv["sender_id"])
            receiver_id = _to_uuid_str(conv["receiver_id"])
            partner_id = receiver_id if sender_id == user_id else sender_id
            product_id = (
                _to_uuid_str(conv["product_id"]) if conv.get("product_id") else None
            )

            # 查询对方用户名
            partner_name = "未知用户"
            partner_avatar = None
            product_name = None
            product_image = None
            async with get_pg() as session:
                partner_user = await users_repo.get_by_id(session, partner_id)
                if partner_user:
                    partner_name = partner_user.username
                    partner_avatar = partner_user.avatar_url
                if product_id:
                    product = await products_repo.get_by_id(session, product_id)
                    if product:
                        product_name = product.name
                        product_image = product.image_url

            items.append(
                ConversationItemOut(
                    partner_user_id=partner_id,
                    partner_name=partner_name,
                    last_message=conv.get("last_message", ""),
                    last_message_type=conv.get("last_message_type", "text"),
                    last_message_at=conv["last_message_at"],
                    unread_count=conv.get("unread_count", 0),
                    avatar_url=partner_avatar,
                    product_id=product_id,
                    product_name=product_name,
                    product_image=product_image,
                )
            )

        return ConversationListOut(items=items)

    async def get_messages(
        self,
        user_id: str,
        partner_user_id: str,
        page: int = 1,
        page_size: int = 30,
        product_id: str | None = None,
    ) -> MessageListOut:
        """获取与某人的消息历史"""
        messages, has_more = await messages_repo.get_messages(
            user_id, partner_user_id, page, page_size, product_id
        )

        items = [
            MessageItemOut(
                id=str(m.id),
                sender_id=str(m.sender_id),
                content=m.content.body,
                content_type=m.content.type,
                product_id=str(m.product_id) if m.product_id else None,
                is_mine=str(m.sender_id) == user_id,
                created_at=m.created_at,
            )
            for m in messages
        ]

        return MessageListOut(items=items, has_more=has_more)

    async def mark_as_read(
        self, user_id: str, partner_user_id: str, product_id: str | None = None
    ) -> int:
        """标记会话已读"""
        return await messages_repo.mark_as_read(user_id, partner_user_id, product_id)

    async def get_unread_count(self, user_id: str) -> int:
        """获取未读消息总数"""
        return await messages_repo.get_unread_count(user_id)
