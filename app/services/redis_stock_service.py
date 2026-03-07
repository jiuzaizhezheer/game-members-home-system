import uuid
from typing import Any, cast

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.repo import products_repo

_DEDUCT_STOCK_LUA = """
local key = KEYS[1]
local qty = tonumber(ARGV[1])

local current = redis.call("GET", key)
if not current then
  return -2
end

local stock = tonumber(current)
if not stock then
  return -3
end

if stock < qty then
  return -1
end

return redis.call("DECRBY", key, qty)
"""

_INCRBY_LUA = """
local key = KEYS[1]
local qty = tonumber(ARGV[1])
return redis.call("INCRBY", key, qty)
"""

_DECRBY_LUA = """
local key = KEYS[1]
local qty = tonumber(ARGV[1])
return redis.call("DECRBY", key, qty)
"""


class RedisStockService:
    def _stock_key(self, product_id: uuid.UUID) -> str:
        return f"stock:{product_id}"

    async def sync_stock_from_db(
        self, redis_client: redis.Redis, session: AsyncSession, product_id: uuid.UUID
    ) -> int:
        product = await products_repo.get_by_id(session, str(product_id))
        if not product:
            raise ValueError("Product not found")
        stock = int(product.stock)
        await redis_client.set(self._stock_key(product_id), stock)
        return stock

    async def ensure_stock_initialized(
        self,
        redis_client: redis.Redis,
        session: AsyncSession,
        product_id: uuid.UUID,
        db_stock: int | None = None,
    ) -> int:
        if db_stock is None:
            product = await products_repo.get_by_id(session, str(product_id))
            if not product:
                raise ValueError("Product not found")
            db_stock = int(product.stock)

        key = self._stock_key(product_id)
        await redis_client.setnx(key, db_stock)
        value = await redis_client.get(key)
        if value is None:
            return db_stock
        return int(value)

    async def try_deduct(
        self,
        redis_client: redis.Redis,
        session: AsyncSession,
        product_id: uuid.UUID,
        quantity: int,
        db_stock: int | None = None,
    ) -> bool:
        if quantity <= 0:
            return True

        await self.ensure_stock_initialized(redis_client, session, product_id, db_stock)
        key = self._stock_key(product_id)
        result = int(
            await cast(Any, redis_client).eval(_DEDUCT_STOCK_LUA, 1, key, quantity)
        )

        if result >= 0:
            return True
        if result == -2:
            await self.sync_stock_from_db(redis_client, session, product_id)
            result = int(
                await cast(Any, redis_client).eval(_DEDUCT_STOCK_LUA, 1, key, quantity)
            )
            return result >= 0
        return False

    async def release(
        self,
        redis_client: redis.Redis,
        session: AsyncSession,
        product_id: uuid.UUID,
        quantity: int,
    ) -> None:
        if quantity <= 0:
            return
        key = self._stock_key(product_id)
        exists = int(await redis_client.exists(key))
        if exists == 0:
            await self.sync_stock_from_db(redis_client, session, product_id)
            return
        await cast(Any, redis_client).eval(_INCRBY_LUA, 1, key, quantity)

    async def compensate_decr(
        self, redis_client: redis.Redis, product_id: uuid.UUID, quantity: int
    ) -> None:
        if quantity <= 0:
            return
        key = self._stock_key(product_id)
        await cast(Any, redis_client).eval(_DECRBY_LUA, 1, key, quantity)


redis_stock_service = RedisStockService()
