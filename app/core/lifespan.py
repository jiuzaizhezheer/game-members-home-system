import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.database import engine
from app.redis import get_redis, redis_pool
from app.services import CaptchaService, UserService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger = logging.getLogger("uvicorn")
    try:
        # 单例模式
        app.state.user_service = UserService()
        app.state.captcha_service = CaptchaService()
        # 初始化pgsql
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("已开启数据库连接")
        # 初始化Redis
        async with get_redis() as redis:
            await redis.ping()  # type: ignore
        logger.info("已开启Redis连接")
        yield
    finally:
        # 关闭pgsql连接
        await engine.dispose()
        logger.info("已关闭pgsql连接")
        # 关闭Redis连接
        await redis_pool.disconnect()
        logger.info("已关闭Redis连接")
