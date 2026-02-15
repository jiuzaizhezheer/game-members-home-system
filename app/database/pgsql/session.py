from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import DATABASE_URL, DEBUG

pg_engine = create_async_engine(
    DATABASE_URL,
    echo=DEBUG,
    future=True,
    pool_size=5,
    max_overflow=5,
    pool_timeout=30,
    pool_recycle=1800,
    # pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=pg_engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False,
)


@asynccontextmanager
async def get_pg() -> AsyncGenerator[AsyncSession, None]:
    """
    会话上下文管理器：事务块自动提交/异常回滚。
    适用于增删改查操作。
    """
    async with AsyncSessionLocal() as session:
        async with session.begin():
            yield session
