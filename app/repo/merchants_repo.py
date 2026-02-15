"""商家仓储层：商家和店铺数据访问"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entity.pgsql import Merchant


async def get_by_user_id(session: AsyncSession, user_id: str) -> Merchant | None:
    """根据用户ID获取商家信息"""
    stmt = select(Merchant).where(Merchant.user_id == user_id)
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_by_id(session: AsyncSession, id: str) -> Merchant | None:
    """根据商家ID获取商家信息"""
    stmt = select(Merchant).where(Merchant.id == id)
    return (await session.execute(stmt)).scalar_one_or_none()


async def update(session: AsyncSession) -> None:
    """更新商家信息"""
    await session.flush()


async def create(session: AsyncSession, merchant: Merchant) -> None:
    """创建商家"""
    session.add(merchant)
