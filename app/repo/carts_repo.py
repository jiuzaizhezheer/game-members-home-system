"""购物车仓储层：购物车数据访问"""

import uuid
from collections.abc import Sequence

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entity.pgsql import Cart, CartItem


async def get_active_by_user_id(session: AsyncSession, user_id: str) -> Cart | None:
    """获取用户当前的活动购物车（最近更新的且未结算的）"""
    stmt = (
        select(Cart)
        .where(Cart.user_id == user_id, ~Cart.is_checked_out)
        .order_by(Cart.updated_at.desc())
        .limit(1)
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_all_by_user_id(session: AsyncSession, user_id: str) -> Sequence[Cart]:
    """获取用户所有购物车"""
    stmt = select(Cart).where(Cart.user_id == user_id).order_by(Cart.created_at.desc())
    return (await session.execute(stmt)).scalars().all()


async def get_by_id(session: AsyncSession, cart_id: uuid.UUID) -> Cart | None:
    """根据ID获取购物车"""
    return await session.get(Cart, cart_id)


async def create(session: AsyncSession, cart: Cart) -> Cart:
    """创建购物车"""
    session.add(cart)
    await session.flush()
    return cart


async def get_items(session: AsyncSession, cart_id: uuid.UUID) -> Sequence[CartItem]:
    """获取购物车明细"""
    stmt = (
        select(CartItem)
        .where(CartItem.cart_id == cart_id)
        .order_by(CartItem.created_at.desc())
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_item_by_product(
    session: AsyncSession, cart_id: uuid.UUID, product_id: uuid.UUID
) -> CartItem | None:
    """获取购物车中的特定商品"""
    stmt = select(CartItem).where(
        CartItem.cart_id == cart_id,
        CartItem.product_id == product_id,
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def add_item(session: AsyncSession, item: CartItem) -> None:
    """添加明细"""
    session.add(item)
    await session.flush()


async def update_item(session: AsyncSession, item: CartItem) -> None:
    """更新明细"""
    await session.flush()  # SQLAlchemy 自动追踪变更，只需 flush


async def delete_item(session: AsyncSession, item: CartItem) -> None:
    """删除明细"""
    await session.delete(item)
    await session.flush()


async def clear_items(session: AsyncSession, cart_id: uuid.UUID) -> None:
    """清空购物车明细"""
    stmt = delete(CartItem).where(CartItem.cart_id == cart_id)
    await session.execute(stmt)
    await session.flush()


async def get_cart_count(session: AsyncSession, cart_id: uuid.UUID) -> int:
    """获取购物车商品种类数量"""
    stmt = select(func.count()).select_from(CartItem).where(CartItem.cart_id == cart_id)
    return (await session.execute(stmt)).scalar() or 0
