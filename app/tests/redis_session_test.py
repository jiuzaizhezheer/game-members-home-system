import asyncio

import pytest
from redis.exceptions import ConnectionError as RedisConnectionError

from app.database.redis import get_redis


@pytest.mark.asyncio(loop_scope="session")
async def test_redis_session_manager():
    """
    测试 Redis 上下文管理器
    """
    print("\nStarting Redis Session Test...")

    try:
        async with get_redis() as redis:
            await redis.ping()
    except RedisConnectionError:
        pytest.skip("Redis 不可用，跳过依赖 Redis 的测试")

    # 1. 测试基本的 set/get
    async with get_redis() as redis:
        test_key = "test:session:manager"
        test_value = "hello_session"

        # Set
        await redis.set(test_key, test_value, ex=10)
        print(f"Set {test_key} = {test_value}")

        # Get
        result = await redis.get(test_key)
        print(f"Get {test_key} = {result}")

        assert result == test_value

        # Delete
        await redis.delete(test_key)
        exists = await redis.exists(test_key)
        assert exists == 0
        print("Delete verification passed")

    # 等待一小段时间让连接释放，避免 Windows 下的 Event loop closed 问题
    await asyncio.sleep(0.1)


if __name__ == "__main__":
    # 如果直接运行此脚本
    asyncio.run(test_redis_session_manager())
