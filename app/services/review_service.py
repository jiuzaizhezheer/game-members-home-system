import uuid
from datetime import UTC, datetime

from app.common.errors import BusinessError, NotFoundError
from app.database.pgsql import get_pg
from app.entity.mongodb import ProductReview
from app.entity.mongodb.product_reviews import ReviewUserRedundancy
from app.repo import merchants_repo, orders_repo, products_repo, users_repo
from app.repo.reviews_repo import reviews_repo
from app.schemas.review import (
    ReviewCreateIn,
    ReviewListOut,
    ReviewOut,
    ReviewReplyIn,
    ReviewUserOut,
)


class ReviewService:
    async def create_review(self, user_id: str, payload: ReviewCreateIn) -> ReviewOut:
        """用户提交商品评价"""
        async with get_pg() as session:
            # 1. 校验订单与商品所属关系与状态
            order = await orders_repo.get_by_id(session, payload.order_id)
            if not order or str(order.user_id) != user_id:
                raise NotFoundError("订单不存在或无权操作")

            if order.status != "completed":
                raise BusinessError(detail="只有已完成的订单才能进行评价")

            # 确认该订单中确实包含此商品
            items = await orders_repo.get_items_by_order_id(session, order.id)
            if not any(str(item.product_id) == payload.product_id for item in items):
                raise BusinessError(detail="该订单中不包含试图评价的商品")

            # 2. 校验是否已评价 (防重复)
            existing_review = await reviews_repo.get_by_order_item(
                payload.order_id, payload.product_id
            )
            if existing_review:
                raise BusinessError(detail="您已经评价过该商品，不能重复评价")

            # 3. 获取用户冗余信息
            user = await users_repo.get_by_id(session, user_id)
            if not user:
                raise NotFoundError("用户不存在")

            # 4. 创建 MongoDB 评价记录
            review_doc = ProductReview(
                product_id=uuid.UUID(payload.product_id),
                order_id=uuid.UUID(payload.order_id),
                user=ReviewUserRedundancy(
                    id=user.id, username=user.username, avatar=user.avatar_url
                ),
                rating=payload.rating,
                content=payload.content,
                images=payload.images or [],
            )
            created_review = await reviews_repo.create(review_doc)

            # 5. 更新 PostgreSQL 中商品的统计字段 (rating 均分 和 review_count)
            product = await products_repo.get_by_id(session, payload.product_id)
            if product:
                # 增量计算新均分: (原始均分 * 原始总数 + 新评分) / (原始总数 + 1)
                # 注: 为防止除零或精度问题，可以这样算
                current_total = product.review_count
                current_rating = product.rating
                new_total = current_total + 1
                new_rating = (
                    (current_rating * current_total) + payload.rating
                ) / new_total

                product.review_count = new_total
                product.rating = new_rating
                await session.flush()

            # Schema 转换: BaseEntity id 是 PydanticObjectId，但 ReviewOut 需为 str
            return ReviewOut(
                id=str(created_review.id),
                product_id=created_review.product_id,
                order_id=created_review.order_id,
                user=ReviewUserOut.model_validate(
                    created_review.user, from_attributes=True
                ),
                rating=created_review.rating,
                content=created_review.content,
                images=created_review.images,
                merchant_reply=created_review.merchant_reply,
                reply_at=created_review.reply_at,
                created_at=created_review.created_at,
                updated_at=created_review.updated_at,
            )

    async def get_product_reviews(
        self, product_id: str, page: int = 1, page_size: int = 10
    ) -> ReviewListOut:
        """获取某商品的评价列表"""
        reviews, total = await reviews_repo.get_list_by_product(
            product_id, page, page_size
        )
        items = [
            ReviewOut(
                id=str(r.id),
                product_id=r.product_id,
                order_id=r.order_id,
                user=ReviewUserOut.model_validate(r.user, from_attributes=True),
                rating=r.rating,
                content=r.content,
                images=r.images,
                merchant_reply=r.merchant_reply,
                reply_at=r.reply_at,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in reviews
        ]
        return ReviewListOut(items=items, total=total, page=page, page_size=page_size)

    async def get_merchant_reviews(
        self, merchant_user_id: str, page: int = 1, page_size: int = 10
    ) -> ReviewListOut:
        """获取商家收到的所有商品评价列表"""
        async with get_pg() as session:
            # 1. 获取商家实体
            merchant = await merchants_repo.get_by_user_id(session, merchant_user_id)
            if not merchant:
                raise BusinessError(detail="当前用户不是商家")

            # 2. 查询属于此商家的所有商品ID (这里取大一点的数字确保能覆盖)
            products, _ = await products_repo.get_list_by_merchant(
                session, str(merchant.id), page_size=1000
            )
            product_ids = [p.id for p in products]

            if not product_ids:
                return ReviewListOut(items=[], total=0, page=page, page_size=page_size)

        # 由于 MongoDB 不能直接 JOIN，我们用 in_ 查询
        from beanie.odm.operators.find.comparison import In

        query = ProductReview.find(In(ProductReview.product_id, product_ids))
        total = await query.count()

        # 按评价时间倒序
        reviews = (
            await query.sort("-created_at")
            .skip((page - 1) * page_size)
            .limit(page_size)
            .to_list()
        )

        items = [
            ReviewOut(
                id=str(r.id),
                product_id=r.product_id,
                order_id=r.order_id,
                user=ReviewUserOut.model_validate(r.user, from_attributes=True),
                rating=r.rating,
                content=r.content,
                images=r.images,
                merchant_reply=r.merchant_reply,
                reply_at=r.reply_at,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in reviews
        ]
        return ReviewListOut(items=items, total=total, page=page, page_size=page_size)

    async def reply_review(
        self, merchant_user_id: str, review_id: str, payload: ReviewReplyIn
    ) -> ReviewOut:
        """商家回复评价"""
        async with get_pg() as session:
            # 1. 校验商家
            merchant = await merchants_repo.get_by_user_id(session, merchant_user_id)
            if not merchant:
                raise BusinessError(detail="当前用户不是商家")

            # 2. 抓取评价
            review = await reviews_repo.get_by_id(review_id)
            if not review:
                raise NotFoundError("评价不存在")

            # 3. 校验该评价对应的商品是否属于此商家
            product = await products_repo.get_by_id(session, str(review.product_id))
            if not product or str(product.merchant_id) != str(merchant.id):
                raise BusinessError(detail="无权回复非本店商品的评价")

            # 4. 仅限首次回复 (本期不做多次追回)
            if review.merchant_reply:
                raise BusinessError(detail="您已经回复过此评价")

            # 5. 更新 MongoDB
            review.merchant_reply = payload.merchant_reply
            review.reply_at = datetime.now(UTC)
            updated_review = await reviews_repo.update(review)

            return ReviewOut(
                id=str(updated_review.id),
                product_id=updated_review.product_id,
                order_id=updated_review.order_id,
                user=ReviewUserOut.model_validate(
                    updated_review.user, from_attributes=True
                ),
                rating=updated_review.rating,
                content=updated_review.content,
                images=updated_review.images,
                merchant_reply=updated_review.merchant_reply,
                reply_at=updated_review.reply_at,
                created_at=updated_review.created_at,
                updated_at=updated_review.updated_at,
            )


review_service = ReviewService()
