import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import jwt

from app.core.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    REFRESH_TOKEN_EXPIRE_DAYS,
    SECRET_KEY,
)
from app.database.redis import get_redis

REFRESH_TOKEN_PREFIX = "refresh_token:"


def get_access_token(user_id: str, role: str) -> str:
    """生成访问令牌"""
    to_encode: dict[str, Any] = {"sub": user_id, "role": role}
    expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """解码访问令牌"""
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return payload


async def get_refresh_token(user_id: str, role: str) -> str:
    """生成刷新令牌"""
    # 生成 refresh_token
    refresh_token = str(uuid.uuid4())
    data = {"user_id": user_id, "role": role}
    # 存储 refresh_token 到 Redis
    async with get_redis() as redis:
        await redis.setex(
            f"{REFRESH_TOKEN_PREFIX}{refresh_token}",
            timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            json.dumps(data),
        )
    return refresh_token


async def verify_refresh_token(refresh_token: str) -> dict | None:
    """
    验证刷新令牌
    如果有效，返回包含 user_id 和 role 的字典
    如果无效或过期，返回 None
    """
    async with get_redis() as redis:
        data = await redis.get(f"{REFRESH_TOKEN_PREFIX}{refresh_token}")
        if data:
            return json.loads(data)
        return None


async def delete_refresh_token(refresh_token: str) -> None:
    """删除刷新令牌"""
    async with get_redis() as redis:
        await redis.delete(f"{REFRESH_TOKEN_PREFIX}{refresh_token}")
