import uuid

_RELEASE_LUA = """
if redis.call("get", KEYS[1]) == ARGV[1] then
  return redis.call("del", KEYS[1])
else
  return 0
end
"""


def new_lock_token() -> str:
    return uuid.uuid4().hex


async def acquire_lock(redis, key: str, *, ttl: int) -> str | None:
    token = new_lock_token()
    ok = await redis.set(key, token, nx=True, ex=ttl)
    return token if ok else None


async def release_lock(redis, key: str, token: str) -> bool:
    res = await redis.eval(_RELEASE_LUA, 1, key, token)
    return bool(res)
