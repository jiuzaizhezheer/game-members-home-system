import uuid
from collections.abc import Sequence
from typing import cast

from sqlalchemy import and_, func, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.entity.pgsql.notifications import SystemNotification


async def create(
    session: AsyncSession, notification: SystemNotification
) -> SystemNotification:
    """创建并保存通知"""
    session.add(notification)
    await session.flush()
    return notification


async def get_unread_count(session: AsyncSession, user_id: uuid.UUID) -> int:
    """获取指定用户的未读消息数量"""
    stmt = select(func.count(SystemNotification.id)).where(
        and_(
            SystemNotification.user_id == user_id, SystemNotification.is_read.is_(False)
        )
    )
    result = await session.execute(stmt)
    return result.scalar() or 0


async def get_list_by_user(
    session: AsyncSession,
    user_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
    notification_type: str | None = None,
) -> tuple[Sequence[SystemNotification], int]:
    """获取用户的消息列表（支持按类型过滤）"""
    stmt = select(SystemNotification).where(SystemNotification.user_id == user_id)

    if notification_type:
        stmt = stmt.where(SystemNotification.type == notification_type)

    # 1. 查询总数
    count_stmt = select(func.count()).select_from(stmt.subquery())
    count_result = await session.execute(count_stmt)
    total = count_result.scalar() or 0

    # 2. 分页查询记录
    stmt = (
        stmt.order_by(SystemNotification.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await session.execute(stmt)
    items = result.scalars().all()

    return items, total


async def get_by_id(
    session: AsyncSession, notification_id: uuid.UUID
) -> SystemNotification | None:
    """根据ID获取通知"""
    stmt = select(SystemNotification).where(SystemNotification.id == notification_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def mark_as_read(session: AsyncSession, notification_id: uuid.UUID) -> bool:
    """将一条消息标记为已读"""
    stmt = (
        update(SystemNotification)
        .where(SystemNotification.id == notification_id)
        .values(is_read=True)
    )
    result = await session.execute(stmt)
    cursor = cast(CursorResult, result)
    return (cursor.rowcount or 0) > 0


async def mark_all_as_read(session: AsyncSession, user_id: uuid.UUID) -> int:
    """将用户的所有消息标记为已读"""
    stmt = (
        update(SystemNotification)
        .where(
            and_(
                SystemNotification.user_id == user_id,
                SystemNotification.is_read.is_(False),
            )
        )
        .values(is_read=True)
    )
    result = await session.execute(stmt)
    cursor = cast(CursorResult, result)
    return cursor.rowcount or 0


async def clear_all_notifications(session: AsyncSession, user_id: uuid.UUID) -> int:
    """清除用户所有系统消息 (预留如果支持删除功能)"""
    from sqlalchemy import delete

    stmt = delete(SystemNotification).where(SystemNotification.user_id == user_id)
    result = await session.execute(stmt)
    cursor = cast(CursorResult, result)
    return cursor.rowcount or 0
