import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.database.session import engine


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    logger = logging.getLogger("app.lifespan")
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("已开启数据库连接")
        yield
    finally:
        await engine.dispose()
        logger.info("已关闭数据库连接")
