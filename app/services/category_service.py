"""分类服务层：分类业务逻辑"""

from app.database.pgsql import get_pg
from app.database.redis import get_redis
from app.repo import categories_repo
from app.schemas.category import CategoryOut
from app.utils.redis_cache import cache_get_json, cache_set_json


class CategoryService:
    """分类服务"""

    async def get_all_categories(self) -> list[CategoryOut]:
        """获取所有分类列表"""
        cache_key = "cache:home:categories:v1"
        async with get_redis() as redis:
            cached = await cache_get_json(redis, cache_key)
            if cached is not None:
                return [CategoryOut.model_validate(x) for x in cached]

        async with get_pg() as session:
            categories = await categories_repo.get_all(session)
            out = [CategoryOut.model_validate(c) for c in categories]

        async with get_redis() as redis:
            await cache_set_json(
                redis,
                cache_key,
                [c.model_dump(mode="json") for c in out],
                ttl=300,
            )
        return out
