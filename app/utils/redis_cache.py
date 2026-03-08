import json
from typing import Any


def dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def loads(value: str) -> Any:
    return json.loads(value)


async def cache_get_json(redis, key: str) -> Any | None:
    raw = await redis.get(key)
    return loads(raw) if raw else None


async def cache_set_json(redis, key: str, value: Any, *, ttl: int) -> None:
    await redis.set(key, dumps(value), ex=ttl)


async def cache_del(redis, *keys: str) -> None:
    if keys:
        await redis.delete(*keys)
