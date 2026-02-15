"""地址仓储层：收货地址数据访问"""

from collections.abc import Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.entity.pgsql import Address


async def get_list_by_user_id(session: AsyncSession, user_id: str) -> Sequence[Address]:
    """获取用户的所有地址"""
    stmt = (
        select(Address)
        .where(Address.user_id == user_id)
        .order_by(Address.is_default.desc(), Address.created_at.desc())
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_by_id(session: AsyncSession, address_id: str) -> Address | None:
    """根据ID获取地址"""
    stmt = select(Address).where(Address.id == address_id)
    return (await session.execute(stmt)).scalar_one_or_none()


async def create(session: AsyncSession, address: Address) -> Address:
    """创建地址"""
    session.add(address)
    await session.flush()
    return address


async def update_address(session: AsyncSession, address: Address) -> Address:
    """更新地址"""
    await session.flush()
    return address


async def delete_address(session: AsyncSession, address: Address) -> None:
    """删除地址"""
    await session.delete(address)
    await session.flush()


async def unset_default_for_user(session: AsyncSession, user_id: str) -> None:
    """取消用户的所有默认地址"""
    stmt = (
        update(Address)
        .where(Address.user_id == user_id, Address.is_default)
        .values(is_default=False)
    )
    await session.execute(stmt)
    await session.flush()


async def get_default_by_user_id(session: AsyncSession, user_id: str) -> Address | None:
    """获取用户的默认地址"""
    stmt = select(Address).where(Address.user_id == user_id, Address.is_default)
    return (await session.execute(stmt)).scalar_one_or_none()
