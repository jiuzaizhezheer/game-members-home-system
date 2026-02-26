import uuid

from beanie.odm.operators.find.comparison import Eq

from app.entity.mongodb import ProductReview


class ReviewsRepo:
    async def create(self, review: ProductReview) -> ProductReview:
        """创建评价"""
        await review.insert()
        return review

    async def get_by_id(self, review_id: str) -> ProductReview | None:
        """根据ID获取评价"""
        return await ProductReview.get(review_id)

    async def get_by_order_item(
        self, order_id: str, product_id: str
    ) -> ProductReview | None:
        """查询某订单下的某个商品是否已被评价 (防重)"""
        return await ProductReview.find_one(
            Eq(ProductReview.order_id, uuid.UUID(order_id)),
            Eq(ProductReview.product_id, uuid.UUID(product_id)),
        )

    async def get_list_by_product(
        self, product_id: str, page: int = 1, page_size: int = 10
    ) -> tuple[list[ProductReview], int]:
        """分页获取某个商品的评价列表"""
        query = ProductReview.find(Eq(ProductReview.product_id, uuid.UUID(product_id)))
        total = await query.count()

        # 按时间倒序
        reviews = (
            await query.sort("-created_at")
            .skip((page - 1) * page_size)
            .limit(page_size)
            .to_list()
        )
        return reviews, total

    async def get_all_list(
        self, page: int = 1, page_size: int = 20, keyword: str | None = None
    ) -> tuple[list[ProductReview], int]:
        """管理员获取全平台评价列表"""
        query = ProductReview.find_all()
        if keyword:
            # 在内容中模糊搜索
            from beanie.odm.operators.find.evaluation import RegEx

            query = query.find(RegEx(ProductReview.content, keyword, options="i"))

        total = await query.count()
        reviews = (
            await query.sort("-created_at")
            .skip((page - 1) * page_size)
            .limit(page_size)
            .to_list()
        )
        return reviews, total

    async def update(self, review: ProductReview) -> ProductReview:
        """更新评价 (主要用于商家回复)"""
        await review.save()
        return review

    async def delete(self, review: ProductReview) -> None:
        """物理删除评价"""
        await review.delete()


reviews_repo = ReviewsRepo()
