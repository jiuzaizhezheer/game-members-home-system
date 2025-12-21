from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

# 获取数据库URL
DATABASE_URL = settings.DATABASE_URL

engine = create_async_engine(
    DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False,
)


# =============================================================================
# 会话上下文管理器（只读/写/嵌套）
# =============================================================================


@asynccontextmanager
async def readonly_session() -> AsyncGenerator[AsyncSession, None]:
    """
    只读会话：不显式提交，存在事务则在结束时回滚。
    适用于纯查询操作。
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except BaseException:
            if session.in_transaction():
                await session.rollback()
            raise
        finally:
            if session.in_transaction():
                await session.rollback()


@asynccontextmanager
async def write_session() -> AsyncGenerator[AsyncSession, None]:
    """
    写会话：事务块自动提交/异常回滚。
    适用于增删改操作。
    """
    async with AsyncSessionLocal() as session:
        async with session.begin():
            yield session


@asynccontextmanager
async def nested_session(
    session: AsyncSession | None = None,
) -> AsyncGenerator[AsyncSession, None]:
    """
    嵌套会话：在已有事务里使用保存点，否则开启顶层事务。
    适用于既可能在事务内调用、又可能独立调用的业务逻辑。
    """
    created = False
    if session is None:
        session = AsyncSessionLocal()
        created = True
    try:
        if session.in_transaction():
            async with session.begin_nested():
                yield session
        else:
            async with session.begin():
                yield session
    finally:
        if created:
            await session.close()
