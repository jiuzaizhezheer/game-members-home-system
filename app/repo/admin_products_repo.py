"""管理员 — 全平台商品与订单查询仓储层"""

import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.entity.pgsql import Order, OrderItem, Product

# --- 商品 ---


async def get_all_products(
    session: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    status: str | None = None,
) -> tuple[list[Product], int]:
    """全平台商品列表（管理员视角，不限定商家）"""
    base = select(Product)

    if keyword:
        base = base.where(Product.name.ilike(f"%{keyword}%"))

    if status:
        base = base.where(Product.status == status)

    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await session.execute(count_stmt)).scalar() or 0

    offset = (page - 1) * page_size
    list_stmt = base.order_by(Product.created_at.desc()).offset(offset).limit(page_size)
    result = await session.execute(list_stmt)
    products = list(result.scalars().all())

    return products, total


async def get_product_by_id(session: AsyncSession, product_id: str) -> Product | None:
    """根据 ID 获取商品"""
    stmt = select(Product).where(Product.id == product_id)
    return (await session.execute(stmt)).scalar_one_or_none()


async def force_offline_product(session: AsyncSession, product_id: str) -> None:
    """强制下架商品"""
    product = await get_product_by_id(session, product_id)
    if product:
        product.status = "off"
        await session.flush()


# --- 订单 ---


async def get_all_orders(
    session: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
) -> tuple[list[Order], int]:
    """全平台订单列表（管理员视角）"""
    base = select(Order).options(selectinload(Order.address))

    if status:
        base = base.where(Order.status == status)

    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await session.execute(count_stmt)).scalar() or 0

    offset = (page - 1) * page_size
    list_stmt = base.order_by(Order.created_at.desc()).offset(offset).limit(page_size)
    result = await session.execute(list_stmt)
    orders = list(result.scalars().all())

    return orders, total


async def get_order_by_id(session: AsyncSession, order_id: str) -> Order | None:
    """根据 ID 获取订单"""
    stmt = (
        select(Order).where(Order.id == order_id).options(selectinload(Order.address))
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_items_by_order_id(
    session: AsyncSession, order_id: uuid.UUID
) -> Sequence[OrderItem]:
    """获取订单明细"""
    stmt = (
        select(OrderItem)
        .where(OrderItem.order_id == order_id)
        .options(selectinload(OrderItem.product))
    )
    result = await session.execute(stmt)
    return result.scalars().all()
