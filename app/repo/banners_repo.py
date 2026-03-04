from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entity.pgsql import Banner


async def get_all(session: AsyncSession, only_active: bool = False) -> list[Banner]:
    """获取所有 Banner"""
    stmt = select(Banner)
    if only_active:
        stmt = stmt.where(Banner.is_active.is_(True))
    stmt = stmt.order_by(Banner.sort_order.desc(), Banner.created_at.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_list_paged(
    session: AsyncSession, page: int = 1, page_size: int = 20
) -> tuple[list[Banner], int]:
    """分页获取 Banner (管理端使用)"""
    stmt = select(Banner)

    # 获取总数
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await session.execute(count_stmt)).scalar() or 0

    # 分页
    offset = (page - 1) * page_size
    stmt = (
        stmt.order_by(Banner.sort_order.desc(), Banner.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all()), total


async def get_by_id(session: AsyncSession, banner_id: str) -> Banner | None:
    """根据ID获取 Banner"""
    stmt = select(Banner).where(Banner.id == banner_id)
    return (await session.execute(stmt)).scalar_one_or_none()


async def create(session: AsyncSession, banner: Banner) -> Banner:
    """创建 Banner"""
    session.add(banner)
    await session.flush()
    return banner


async def delete(session: AsyncSession, banner: Banner) -> None:
    """删除 Banner"""
    await session.delete(banner)
    await session.flush()
