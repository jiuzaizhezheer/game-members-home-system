import uuid
from types import SimpleNamespace
from typing import Any, cast

import pytest

from app.services.redis_stock_service import (
    _DECRBY_LUA,
    _DEDUCT_STOCK_LUA,
    _INCRBY_LUA,
    redis_stock_service,
)


class FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, int] = {}

    async def set(self, key: str, value: Any) -> None:
        self.store[key] = int(value)

    async def setnx(self, key: str, value: Any) -> int:
        if key in self.store:
            return 0
        self.store[key] = int(value)
        return 1

    async def get(self, key: str) -> str | None:
        if key not in self.store:
            return None
        return str(self.store[key])

    async def exists(self, key: str) -> int:
        return 1 if key in self.store else 0

    async def eval(self, script: str, numkeys: int, key: str, quantity: int) -> int:
        qty = int(quantity)
        if script == _DEDUCT_STOCK_LUA:
            if key not in self.store:
                return -2
            stock = int(self.store[key])
            if stock < qty:
                return -1
            self.store[key] = stock - qty
            return self.store[key]
        if script == _INCRBY_LUA:
            self.store[key] = int(self.store.get(key, 0)) + qty
            return self.store[key]
        if script == _DECRBY_LUA:
            self.store[key] = int(self.store.get(key, 0)) - qty
            return self.store[key]
        raise ValueError("Unknown script")


@pytest.mark.asyncio(loop_scope="session")
async def test_try_deduct_success_without_db_query(monkeypatch: pytest.MonkeyPatch):
    r = cast(Any, FakeRedis())
    session = cast(Any, object())
    product_id = uuid.uuid4()
    key = f"stock:{product_id}"

    r.store[key] = 5

    async def _no_call(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Should not query DB")

    monkeypatch.setattr("app.repo.products_repo.get_by_id", _no_call)

    ok = await redis_stock_service.try_deduct(r, session, product_id, 3, db_stock=5)
    assert ok is True
    assert r.store[key] == 2


@pytest.mark.asyncio(loop_scope="session")
async def test_try_deduct_fail_when_insufficient():
    r = cast(Any, FakeRedis())
    session = cast(Any, object())
    product_id = uuid.uuid4()
    key = f"stock:{product_id}"

    r.store[key] = 2
    ok = await redis_stock_service.try_deduct(r, session, product_id, 3, db_stock=2)
    assert ok is False
    assert r.store[key] == 2


@pytest.mark.asyncio(loop_scope="session")
async def test_release_increments_when_key_exists():
    r = cast(Any, FakeRedis())
    session = cast(Any, object())
    product_id = uuid.uuid4()
    key = f"stock:{product_id}"

    r.store[key] = 2
    await redis_stock_service.release(r, session, product_id, 3)
    assert r.store[key] == 5


@pytest.mark.asyncio(loop_scope="session")
async def test_release_syncs_when_key_missing(monkeypatch: pytest.MonkeyPatch):
    r = cast(Any, FakeRedis())
    product_id = uuid.uuid4()
    key = f"stock:{product_id}"
    session = cast(Any, object())

    async def _fake_get_by_id(*args: Any, **kwargs: Any) -> Any:
        return SimpleNamespace(stock=10)

    monkeypatch.setattr("app.repo.products_repo.get_by_id", _fake_get_by_id)

    await redis_stock_service.release(r, session, product_id, 3)
    assert r.store[key] == 10
