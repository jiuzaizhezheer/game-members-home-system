"""收藏服务层：收藏业务逻辑"""

import uuid

from app.common.errors import NotFoundError
from app.database.pgsql import get_pg
from app.repo import favorites_repo, products_repo
from app.schemas.favorite import FavoriteCheckOut, FavoriteItemOut, FavoriteListOut


class FavoriteService:
    """收藏服务"""

    async def add_favorite(self, user_id: str, product_id: str) -> None:
        """添加收藏（幂等：已收藏时静默成功）"""
        uid = uuid.UUID(user_id)
        pid = uuid.UUID(product_id)
        async with get_pg() as session:
            # 检查商品存在
            product = await products_repo.get_by_id(session, product_id)
            if not product:
                raise NotFoundError("商品不存在")

            # 幂等：已收藏则直接返回
            already = await favorites_repo.check(session, uid, pid)
            if already:
                return

            await favorites_repo.add(session, uid, pid)

    async def remove_favorite(self, user_id: str, product_id: str) -> None:
        """取消收藏"""
        uid = uuid.UUID(user_id)
        pid = uuid.UUID(product_id)
        async with get_pg() as session:
            await favorites_repo.remove(session, uid, pid)

    async def remove_batch(self, user_id: str, product_ids: list[uuid.UUID]) -> None:
        """批量取消收藏"""
        uid = uuid.UUID(user_id)
        async with get_pg() as session:
            await favorites_repo.remove_batch(session, uid, product_ids)

    async def get_favorites(
        self, user_id: str, page: int = 1, page_size: int = 20
    ) -> FavoriteListOut:
        """获取收藏列表"""
        uid = uuid.UUID(user_id)
        async with get_pg() as session:
            rows, total = await favorites_repo.get_list(
                session, uid, page=page, page_size=page_size
            )
            items = [
                FavoriteItemOut(
                    product_id=fav.product_id,
                    product_name=product.name,
                    product_image=product.image_url,
                    product_price=product.price,
                    product_status=product.status,
                    created_at=fav.created_at,
                )
                for fav, product in rows
            ]
            return FavoriteListOut(
                items=items, total=total, page=page, page_size=page_size
            )

    async def check_favorited(self, user_id: str, product_id: str) -> FavoriteCheckOut:
        """检查收藏状态"""
        uid = uuid.UUID(user_id)
        pid = uuid.UUID(product_id)
        async with get_pg() as session:
            is_fav = await favorites_repo.check(session, uid, pid)
            return FavoriteCheckOut(is_favorited=is_fav)
