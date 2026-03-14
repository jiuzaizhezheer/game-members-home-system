"""管理员 — 用户与商家查询仓储层"""

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entity.pgsql import User


async def get_user_list(
    session: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
) -> tuple[list[User], int]:
    """分页查询用户列表（支持搜索、角色、状态筛选）"""
    base = select(User)

    if keyword:
        like_pattern = f"%{keyword}%"
        base = base.where(
            or_(User.username.ilike(like_pattern), User.email.ilike(like_pattern))
        )

    if role is not None:
        base = base.where(User.role == role)

    if is_active is not None:
        base = base.where(User.is_active == is_active)

    # 总数
    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await session.execute(count_stmt)).scalar() or 0

    # 分页
    offset = (page - 1) * page_size
    list_stmt = base.order_by(User.created_at.desc()).offset(offset).limit(page_size)
    result = await session.execute(list_stmt)
    users = list(result.scalars().all())

    return users, total


async def get_user_by_id(session: AsyncSession, user_id: str) -> User | None:
    """根据 ID 获取用户"""
    stmt = select(User).where(User.id == user_id)
    return (await session.execute(stmt)).scalar_one_or_none()


async def set_user_active(session: AsyncSession, user_id: str, is_active: bool) -> None:
    """启用/禁用用户"""
    user = await get_user_by_id(session, user_id)
    if user:
        user.is_active = is_active
        await session.flush()
