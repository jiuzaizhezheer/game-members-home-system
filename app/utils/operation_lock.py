from app.database.redis.session import get_redis


async def check_operation_lock(key: str, expired: int) -> bool:
    """
    检查操作锁 (防重复操作/防刷)

    :param key: 锁的唯一键 (如 viewed:post:123:user:456)
    :param expired: 锁过期时间（秒）
    :return:
        True:  锁存在 -> 表示操作受限/已操作过
        False: 锁不存在 -> 表示可以操作 (随后会自动上锁)
    """
    async with get_redis() as redis:
        # 1. 尝试获取锁
        if await redis.get(key):
            return True

        # 2. 如果没锁，上锁并设置过期时间
        await redis.setex(key, expired, "1")
        return False
