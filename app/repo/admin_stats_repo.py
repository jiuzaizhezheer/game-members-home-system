"""管理员平台级统计仓储层"""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entity.pgsql import Order, Post, Product, User


async def get_platform_stats(session: AsyncSession) -> dict[str, Any]:
    """获取平台级统计概览数据"""

    # 1. 会员总数
    total_users = (
        await session.execute(
            select(func.count(User.id)).where(
                User.role == "member", User.is_active.is_(True)
            )
        )
    ).scalar() or 0

    # 2. 商家总数
    total_merchants = (
        await session.execute(
            select(func.count(User.id)).where(
                User.role == "merchant", User.is_active.is_(True)
            )
        )
    ).scalar() or 0

    # 3. 商品总数（不含已删除）
    total_products = (
        await session.execute(
            select(func.count(Product.id)).where(Product.status != "deleted")
        )
    ).scalar() or 0

    # 4. 订单总数（不含已取消）
    total_orders = (
        await session.execute(
            select(func.count(Order.id)).where(Order.status != "cancelled")
        )
    ).scalar() or 0

    # 5. 帖子总数（作为待审核基数）
    pending_audits = (await session.execute(select(func.count(Post.id)))).scalar() or 0

    return {
        "total_users": total_users,
        "total_merchants": total_merchants,
        "total_products": total_products,
        "total_orders": total_orders,
        "pending_audits": pending_audits,
    }
