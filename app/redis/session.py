from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import redis.asyncio as redis

from app.core.config import REDIS_URL

redis_pool = redis.ConnectionPool.from_url(
    REDIS_URL, decode_responses=True, max_connections=5
)


def get_client() -> redis.Redis:
    """
    获取一个 Redis 客户端实例
    """
    return redis.Redis(connection_pool=redis_pool)


@asynccontextmanager
async def get_redis() -> AsyncGenerator[redis.Redis, None]:
    """
    Redis 客户端上下文管理器（用于依赖注入或 with 语句）

    Usage:
        async with get_redis() as redis:
            await redis.set("key", "value")
    """
    client = get_client()
    try:
        yield client
    finally:
        # redis-py 的客户端会自动管理连接释放回池
        await client.aclose()
