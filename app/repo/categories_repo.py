"""分类仓储层：分类数据访问"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entity import Category


async def get_all(session: AsyncSession) -> list[Category]:
    """获取所有分类"""
    stmt = select(Category).order_by(Category.name)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_by_id(session: AsyncSession, category_id: str) -> Category | None:
    """根据ID获取分类"""
    stmt = select(Category).where(Category.id == category_id)
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_by_ids(session: AsyncSession, category_ids: list[str]) -> list[Category]:
    """根据ID列表获取分类"""
    if not category_ids:
        return []
    stmt = select(Category).where(Category.id.in_(category_ids))
    result = await session.execute(stmt)
    return list(result.scalars().all())
