import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entity.pgsql import OrderLogistics


async def add_log(session: AsyncSession, log: OrderLogistics) -> OrderLogistics:
    """添加一条物流轨迹"""
    session.add(log)
    await session.flush()
    return log


async def get_by_order_id(
    session: AsyncSession, order_id: uuid.UUID | str
) -> list[OrderLogistics]:
    """获取订单的所有物流轨迹"""
    stmt = (
        select(OrderLogistics)
        .where(OrderLogistics.order_id == order_id)
        .order_by(OrderLogistics.log_time.asc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())
