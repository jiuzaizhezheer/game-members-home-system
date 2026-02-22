"""收藏仓储层：收藏数据访问"""

import uuid
from collections.abc import Sequence

from sqlalchemy import delete as sa_delete
from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entity.pgsql import Favorite, Product
from app.repo import products_repo


async def add(session: AsyncSession, user_id: uuid.UUID, product_id: uuid.UUID) -> None:
    """添加收藏"""
    fav = Favorite(user_id=user_id, product_id=product_id)
    session.add(fav)
    await session.flush()
    # 同步更新商品收藏量
    await products_repo.change_favorites_count(session, product_id, 1)


async def remove(
    session: AsyncSession, user_id: uuid.UUID, product_id: uuid.UUID
) -> None:
    """取消收藏"""
    stmt = sa_delete(Favorite).where(
        Favorite.user_id == user_id, Favorite.product_id == product_id
    )
    await session.execute(stmt)
    await session.flush()
    # 同步更新商品收藏量
    await products_repo.change_favorites_count(session, product_id, -1)


async def remove_batch(
    session: AsyncSession, user_id: uuid.UUID, product_ids: list[uuid.UUID]
) -> None:
    """批量取消收藏"""
    stmt = sa_delete(Favorite).where(
        Favorite.user_id == user_id, Favorite.product_id.in_(product_ids)
    )
    await session.execute(stmt)
    await session.flush()
    # 同步更新商品收藏量
    for pid in product_ids:
        await products_repo.change_favorites_count(session, pid, -1)


async def get_list(
    session: AsyncSession,
    user_id: uuid.UUID,
    *,
    page: int = 1,
    page_size: int = 20,
) -> tuple[Sequence[tuple[Favorite, Product]], int]:
    """获取用户收藏列表（分页，JOIN 商品表）"""
    base_stmt = (
        select(Favorite, Product)
        .join(Product, Favorite.product_id == Product.id)
        .where(Favorite.user_id == user_id)
    )

    # 总数
    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = (await session.execute(count_stmt)).scalar() or 0

    # 分页
    offset = (page - 1) * page_size
    list_stmt = (
        base_stmt.order_by(Favorite.created_at.desc()).offset(offset).limit(page_size)
    )
    result = await session.execute(list_stmt)
    rows = result.tuples().all()

    return rows, total


async def check(
    session: AsyncSession, user_id: uuid.UUID, product_id: uuid.UUID
) -> bool:
    """检查是否已收藏"""
    stmt = select(
        exists().where(Favorite.user_id == user_id, Favorite.product_id == product_id)
    )
    return bool((await session.execute(stmt)).scalar())
