import uuid

from app.common.errors import NotFoundError
from app.database.pgsql.session import get_pg
from app.entity.pgsql.promotions import Promotion
from app.repo import promotions_repo
from app.schemas.product import ProductPublicOut
from app.schemas.promotion import (
    PromotionCreateIn,
    PromotionDetailOut,
    PromotionListOut,
    PromotionOut,
    PromotionUpdateIn,
)


class PromotionService:
    async def create_promotion(
        self, merchant_id: uuid.UUID, data: PromotionCreateIn
    ) -> PromotionOut:
        async with get_pg() as session:
            promotion = Promotion(
                merchant_id=merchant_id,
                title=data.title,
                discount_type=data.discount_type,
                discount_value=data.discount_value,
                start_at=data.start_at,
                end_at=data.end_at,
                status=data.status,
            )

            new_promotion = await promotions_repo.create_promotion(
                session, promotion, data.product_ids
            )
            return PromotionOut.model_validate(new_promotion)

    async def update_promotion(
        self, merchant_id: uuid.UUID, promotion_id: uuid.UUID, data: PromotionUpdateIn
    ) -> PromotionOut:
        async with get_pg() as session:
            existing = await promotions_repo.get_promotion_by_id(session, promotion_id)
            if not existing or existing.merchant_id != merchant_id:
                raise NotFoundError("Promotion not found")

            update_data = data.model_dump(exclude_unset=True)
            product_ids = update_data.pop("product_ids", None)

            updated_promotion = await promotions_repo.update_promotion(
                session, promotion_id, product_ids, **update_data
            )

            if not updated_promotion:
                raise NotFoundError("Promotion not found after update")

            return PromotionOut.model_validate(updated_promotion)

    async def delete_promotion(
        self, merchant_id: uuid.UUID, promotion_id: uuid.UUID
    ) -> None:
        async with get_pg() as session:
            existing = await promotions_repo.get_promotion_by_id(session, promotion_id)
            if not existing or existing.merchant_id != merchant_id:
                raise NotFoundError("Promotion not found")

            await promotions_repo.delete_promotion(session, promotion_id)

    async def get_promotion(
        self, merchant_id: uuid.UUID, promotion_id: uuid.UUID
    ) -> PromotionDetailOut:
        async with get_pg() as session:
            existing = await promotions_repo.get_promotion_by_id(session, promotion_id)
            if not existing or existing.merchant_id != merchant_id:
                raise NotFoundError("Promotion not found")

            products = await promotions_repo.get_promotion_products(
                session, promotion_id
            )

            return PromotionDetailOut(
                **PromotionOut.model_validate(existing).model_dump(),
                products=[ProductPublicOut.model_validate(p) for p in products],
            )

    async def list_promotions(
        self, merchant_id: uuid.UUID, page: int = 1, page_size: int = 20
    ) -> PromotionListOut:
        async with get_pg() as session:
            items, total = await promotions_repo.get_merchant_promotions(
                session, merchant_id, page, page_size
            )

            return PromotionListOut(
                items=[PromotionOut.model_validate(item) for item in items],
                total=total,
                page=page,
                page_size=page_size,
            )

    async def get_active_promotions_by_product_ids(
        self, product_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, Promotion]:
        """获取商品的最佳有效促销活动"""
        async with get_pg() as session:
            rows = await promotions_repo.get_active_promotions_by_product_ids(
                session, product_ids
            )

            best_promotions: dict[uuid.UUID, Promotion] = {}
            for product_id, promotion in rows:
                # 如果该商品还没有促销，或者当前促销比已有的更好（这里简化为：覆盖即可，因为 SQL 已经按创建时间倒序，
                # 但更严谨的应该是比较优惠力度。鉴于需求简单，暂以最新创建为准，或后续添加优先级逻辑）
                # 实际上 repo 返回的是 (product_id, promotion)
                # 由于我们按 created_at desc 排序，第一个遇到的（即最新的）就是我们想要的
                # 或者我们可以比较 discount_value.

                if product_id not in best_promotions:
                    best_promotions[product_id] = promotion
                else:
                    # 比较优惠力度 (粗略比较: 百分比越小越好? 不, fixed 越大越好, percent 越大越好 (例如 20% OFF))
                    # percent: 20 -> 20% OFF
                    # fixed: 10 -> 减 10
                    # 很难直接比较不同类型的优惠。
                    # 简单起见：优先取 discount_value 大的?
                    # 还是维持 "最新优先" 策略?
                    # 让我们使用 "最新优先" (SQL 已排序), 所以保留第一个遇到的即可。
                    pass

            return best_promotions
