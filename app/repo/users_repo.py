from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entity import User


# 检查用户名或邮箱是否已存在
async def exists_by_username_or_email(
    session: AsyncSession, username: str, email: str
) -> bool:
    stmt = select(
        exists().where(
            (User.is_active.is_(True))
            & ((User.username == username) | (User.email == email))
        )
    )
    return bool(await session.scalar(stmt))


# 插入用户
async def insert(session: AsyncSession, user: User) -> User:
    session.add(user)
    await session.flush()
    return user


# async def get_by_username(session: AsyncSession, username: str) -> User | None:
#     stmt = select(User).where(User.username == username)
#     return (await session.execute(stmt)).scalar_one_or_none()


# async def update_password_hash(session: AsyncSession, user: User, password_hash: str) -> None:
#     user.password_hash = password_hash
#     await session.flush()
