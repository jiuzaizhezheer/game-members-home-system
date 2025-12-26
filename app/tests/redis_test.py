import asyncio

import redis.asyncio as redis

# Redis 连接配置
REDIS_URL = "redis://localhost:6379/8"


async def redis_demo():
    print(f"Connecting to Redis at {REDIS_URL}...")
    # 1. 创建 Redis 客户端
    client = redis.from_url(REDIS_URL, decode_responses=True)

    try:
        # --- Create (设置值) ---
        print("\n[CREATE] Setting key 'test_key' with value 'hello_redis'...")
        await client.set("test_key", "hello_redis", ex=60)  # 设置 60 秒过期

        # --- Read (读取值) ---
        print("[READ] Getting value for 'test_key'...")
        value = await client.get("test_key")
        print(f"Result: {value}")

        # --- Update (更新值) ---
        print("\n[UPDATE] Updating 'test_key' to 'updated_value'...")
        await client.set("test_key", "updated_value")
        new_value = await client.get("test_key")
        print(f"New Result: {new_value}")

        # --- Exists (检查是否存在) ---
        print("\n[CHECK] Checking if 'test_key' exists...")
        is_exists = await client.exists("test_key")
        print(f"Exists: {bool(is_exists)}")

        # --- Delete (删除值) ---
        print("\n[DELETE] Deleting 'test_key'...")
        await client.delete("test_key")

        # 再次确认
        is_exists_after = await client.exists("test_key")
        print(f"Exists after delete: {bool(is_exists_after)}")

    except Exception as e:
        print(f"An error occurred: {e}")
        print("\n提示: 请确保 Redis 服务已启动并在 localhost:6379 运行。")
        print("如果未安装 redis 库，请运行: pdm add redis")
    finally:
        # 关闭连接
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(redis_demo())
