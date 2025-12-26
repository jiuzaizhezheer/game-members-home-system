import asyncio

import pytest

from app.redis import get_redis


@pytest.mark.asyncio
async def test_redis_session_manager():
    """
    测试 Redis 上下文管理器
    """
    print("\nStarting Redis Session Test...")

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


if __name__ == "__main__":
    # 如果直接运行此脚本
    asyncio.run(test_redis_session_manager())
