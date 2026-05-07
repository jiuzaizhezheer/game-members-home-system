"""消息仓储层：MongoDB 消息数据访问（基于 Beanie）"""

from collections.abc import Mapping, Sequence
from typing import Any, cast
from uuid import UUID

from bson import Binary

from app.entity.mongodb import Message, MessageContent


def _make_conversation_id(
    user_a: str, user_b: str, product_id: str | None = None
) -> str:
    """生成会话 ID：将两个用户 ID 排序后拼接，保证同一对用户始终同一个会话"""
    ids = sorted([user_a, user_b])
    base = f"{ids[0]}_{ids[1]}"
    return f"{base}_product_{product_id}" if product_id else base


def _product_match(product_id: str | None) -> dict[str, Any]:
    if product_id:
        return {"product_id": Binary.from_uuid(UUID(product_id))}
    return {"$or": [{"product_id": None}, {"product_id": {"$exists": False}}]}


async def send_message(
    sender_id: UUID,
    receiver_id: UUID,
    content: str,
    content_type: str = "text",
    product_id: UUID | None = None,
    order_id: UUID | None = None,
) -> Message:
    """保存一条消息"""
    conversation_id = _make_conversation_id(
        str(sender_id), str(receiver_id), str(product_id) if product_id else None
    )
    msg = Message(
        conversation_id=conversation_id,
        sender_id=sender_id,
        receiver_id=receiver_id,
        product_id=product_id,
        order_id=order_id,
        content=MessageContent(type=content_type, body=content),
        is_read=False,
    )
    await msg.insert()
    return msg


async def get_conversations(user_id: str) -> list[dict]:
    """
    获取用户的会话列表
    聚合查询：按 conversation_id 分组，取最新消息和未读数
    """
    pipeline: Sequence[Mapping[str, Any]] = [
        # 过滤出当前用户参与的会话（且未被删除）
        {
            "$match": {
                "$or": [
                    {"sender_id": Binary.from_uuid(UUID(user_id))},
                    {"receiver_id": Binary.from_uuid(UUID(user_id))},
                ],
                "deleted_by": {"$nin": [Binary.from_uuid(UUID(user_id))]},
            }
        },
        # 按 conversation_id 分组
        {"$sort": {"created_at": -1}},
        {
            "$group": {
                "_id": "$conversation_id",
                "last_message": {"$first": "$content.body"},
                "last_message_type": {"$first": "$content.type"},
                "last_message_at": {"$first": "$created_at"},
                "sender_id": {"$first": "$sender_id"},
                "receiver_id": {"$first": "$receiver_id"},
                "product_id": {"$first": "$product_id"},
                "unread_count": {
                    "$sum": {
                        "$cond": [
                            {
                                "$and": [
                                    {
                                        "$eq": [
                                            "$receiver_id",
                                            Binary.from_uuid(UUID(user_id)),
                                        ]
                                    },
                                    {"$eq": ["$is_read", False]},
                                ]
                            },
                            1,
                            0,
                        ]
                    }
                },
            }
        },
        {"$sort": {"last_message_at": -1}},
    ]

    collection = cast(Any, Message.get_pymongo_collection())
    return await collection.aggregate(pipeline).to_list(length=None)


async def get_messages(
    user_id: str,
    partner_user_id: str,
    page: int = 1,
    page_size: int = 30,
    product_id: str | None = None,
) -> tuple[list[Message], bool]:
    """分页获取会话消息（最新在后）"""
    conversation_id = _make_conversation_id(user_id, partner_user_id, product_id)
    query = Message.find(
        Message.conversation_id == conversation_id,
        _product_match(product_id),
        {"deleted_by": {"$nin": [UUID(user_id)]}},
    )

    total = await query.count()
    has_more = total > page * page_size

    # 按创建时间降序取 page_size 条，再反转显示
    skip = (page - 1) * page_size
    messages = (
        await Message.find(
            Message.conversation_id == conversation_id,
            _product_match(product_id),
            {"deleted_by": {"$nin": [UUID(user_id)]}},
        )
        .sort("-created_at")
        .skip(skip)
        .limit(page_size)
        .to_list()
    )
    messages.reverse()  # 最早的在前

    return messages, has_more


async def mark_as_read(
    user_id: str, partner_user_id: str, product_id: str | None = None
) -> int:
    """标记会话中发给自己的消息为已读"""
    conversation_id = _make_conversation_id(user_id, partner_user_id, product_id)
    result = cast(
        Any,
        await Message.find(
            Message.conversation_id == conversation_id,
            Message.receiver_id == UUID(user_id),
            Message.is_read == False,  # noqa: E712
            _product_match(product_id),
        ).update_many({"$set": {"is_read": True}}),
    )
    if result is None:
        return 0
    return result.modified_count


async def get_unread_count(user_id: str) -> int:
    """获取用户总未读消息数"""
    count = await Message.find(
        Message.receiver_id == UUID(user_id),
        Message.is_read == False,  # noqa: E712
        {"deleted_by": {"$nin": [UUID(user_id)]}},
    ).count()
    return count
