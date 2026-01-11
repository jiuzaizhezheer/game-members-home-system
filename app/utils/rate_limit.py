from fastapi import HTTPException, Request, status

from app.common.constants import TOO_MANY_REQUESTS
from app.redis.session import get_redis


class RateLimiter:
    """
    基于 Redis 的简单限流器
    """

    def __init__(self, counts: int, seconds: int):
        self.counts = counts
        self.seconds = seconds

    async def __call__(self, request: Request):
        # 1. 优先根据 User ID 限流 (针对已登录用户)
        user_id = getattr(request.state, "user_id", None)

        if user_id:
            identifier = f"user:{user_id}"
        else:
            # 2. 其次, 未登录用户根据真实 IP 限流
            # TODO: 基于IP的限流(粒度过大), 后续可修改为匿名设备ID（服务端生成）+ Session返回给前端 + IP 兜底
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                ip = forwarded.split(",")[0].strip()
            else:
                ip = request.headers.get("X-Real-IP") or (
                    request.client.host if request.client else "unknown"
                )
            identifier = f"ip:{ip}"

        key = f"rate_limit:{request.url.path}:{identifier}"

        # 使用 Redis 计数
        async with get_redis() as redis:
            # 增加计数并设置过期时间
            # 使用 pipeline 保证原子性
            # 滑动窗口限流: 必须完全间隔seconds时间窗口, 才能再次请求
            pipe = redis.pipeline()
            await pipe.incr(key)
            await pipe.expire(key, self.seconds)
            # 返回的结果是一个列表，每个命令的结果按顺序排列
            results = await pipe.execute()
            # 第一个结果是 incr 命令的结果, 即当前请求的计数
            count = results[0]

            if count > self.counts:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=TOO_MANY_REQUESTS,
                )
