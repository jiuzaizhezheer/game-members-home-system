import uuid

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entity.pgsql.point_logs import PointLog


async def add_log(session: AsyncSession, log: PointLog) -> PointLog:
    """添加积分变动记录"""
    session.add(log)
    await session.flush()
    return log


async def get_by_user_id(
    session: AsyncSession, user_id: uuid.UUID, page: int = 1, page_size: int = 10
) -> tuple[list[PointLog], int]:
    """获取用户的积分变动记录"""
    offset = (page - 1) * page_size

    # 1. 查询总数
    count_stmt = (
        select(func.count()).select_from(PointLog).where(PointLog.user_id == user_id)
    )
    total = await session.scalar(count_stmt) or 0

    # 2. 查询明细
    stmt = (
        select(PointLog)
        .where(PointLog.user_id == user_id)
        .order_by(desc(PointLog.created_at))
        .offset(offset)
        .limit(page_size)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all()), total
