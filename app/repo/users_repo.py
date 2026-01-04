from sqlalchemy import exists, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entity import User


async def exists_by_username_or_email(
    session: AsyncSession, username: str, email: str
) -> bool:
    """检查用户名或邮箱是否已存在"""
    stmt = select(
        exists().where(
            User.is_active.is_(True),
            or_(
                User.username == username,
                User.email == email,
            ),
        )
    )
    return bool(await session.scalar(stmt))


# 插入用户
async def create(session: AsyncSession, user: User) -> None:
    """创建用户"""
    session.add(user)


async def get_by_username(session: AsyncSession, username: str) -> User | None:
    """根据用户名查询用户"""
    stmt = select(User).where(User.is_active.is_(True), User.username == username)
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_by_email(session: AsyncSession, email: str) -> User | None:
    """根据邮箱查询用户"""
    stmt = select(User).where(User.is_active.is_(True), User.email == email)
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_by_id(session: AsyncSession, user_id: str) -> User | None:
    """根据用户ID查询用户"""
    stmt = select(User).where(User.is_active.is_(True), User.id == user_id)
    return (await session.execute(stmt)).scalar_one_or_none()


async def update_password_hash(
    session: AsyncSession, user: User, password_hash: str
) -> None:
    """更新用户密码哈希"""
    user.password_hash = password_hash
    await session.flush()
