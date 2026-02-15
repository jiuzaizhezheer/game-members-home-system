"""订单仓储层：订单及其明细数据访问"""

import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.entity.pgsql import Order, OrderItem, Product


async def create(session: AsyncSession, order: Order) -> Order:
    """创建订单"""
    session.add(order)
    await session.flush()
    return order


async def add_items(session: AsyncSession, items: list[OrderItem]) -> None:
    """批量添加订单明细"""
    session.add_all(items)
    await session.flush()


async def get_by_id(session: AsyncSession, order_id: str) -> Order | None:
    """根据ID获取订单（包含明细）"""
    # 同样地，如果 Entity 没定义 relationship，我们需要手动加载或补充
    # 假设需要 selectinload
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


async def get_list_by_user(
    session: AsyncSession, user_id: str, page: int = 1, page_size: int = 10
) -> tuple[list[Order], int]:
    """分页获取用户的订单列表"""
    base_stmt = (
        select(Order)
        .where(Order.user_id == user_id)
        .options(selectinload(Order.address))
    )

    # 获取总数
    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = (await session.execute(count_stmt)).scalar() or 0

    # 分页查询
    offset = (page - 1) * page_size
    list_stmt = (
        base_stmt.order_by(Order.created_at.desc()).offset(offset).limit(page_size)
    )
    result = await session.execute(list_stmt)
    orders = list(result.scalars().all())

    return orders, total


async def get_list_by_merchant(
    session: AsyncSession,
    merchant_id: str,
    page: int = 1,
    page_size: int = 10,
    status: str | None = None,
) -> tuple[list[Order], int]:
    """分页获取商家的订单列表 (通过订单明细关联商品)"""
    # 基础查询: 查找包含该商家商品的订单ID
    base_stmt = (
        select(Order)
        .join(OrderItem, OrderItem.order_id == Order.id)
        .join(Product, Product.id == OrderItem.product_id)
        .where(Product.merchant_id == merchant_id)
        .options(selectinload(Order.address))
    )

    # 状态筛选
    if status:
        base_stmt = base_stmt.where(Order.status == status)

    base_stmt = base_stmt.distinct()

    # 获取总数
    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = (await session.execute(count_stmt)).scalar() or 0

    # 分页查询
    offset = (page - 1) * page_size
    list_stmt = (
        base_stmt.order_by(Order.created_at.desc()).offset(offset).limit(page_size)
    )
    result = await session.execute(list_stmt)
    orders = list(result.scalars().all())

    return orders, total


async def get_shipped_orders_before(
    session: AsyncSession, before_time
) -> Sequence[Order]:
    """获取指定时间之前且状态为已发货的订单"""
    stmt = (
        select(Order)
        .where(Order.status == "shipped")  # 已发货
        .where(Order.shipped_at < before_time)
    )
    result = await session.execute(stmt)
    return result.scalars().all()
