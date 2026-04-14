import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.database.mongodb import init_mongodb, mongodb_client
from app.database.pgsql import pg_engine
from app.database.redis import get_redis, redis_pool
from app.tasks.broker import broker


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger = logging.getLogger("uvicorn")
    try:
        # 初始化pgsql
        async with pg_engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("已开启Pgsql连接")
        # 初始化MongoDB
        await init_mongodb()
        await mongodb_client.admin.command("ping")
        logger.info("已开启MongoDB连接")
        # 初始化Redis
        async with get_redis() as redis:
            await redis.ping()  # type: ignore
        # 初始化Taskiq Broker
        await broker.startup()
        logger.info("已开启Taskiq Broker")
        yield
    finally:
        # 关闭pgsql连接
        await pg_engine.dispose()
        logger.info("已关闭Pgsql连接")
        # 关闭MongoDB连接
        mongodb_client.close()
        logger.info("已关闭MongoDB连接")
        # 关闭Redis连接
        await redis_pool.disconnect()
        logger.info("已关闭Redis连接")
        # 关闭Taskiq Broker
        await broker.shutdown()
        logger.info("已关闭Taskiq Broker")
