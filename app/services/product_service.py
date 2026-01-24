"""商品服务层：商品业务逻辑"""

from app.common.constants import (
    MERCHANT_NOT_FOUND,
    PRODUCT_NOT_FOUND,
    PRODUCT_SKU_EXISTS,
)
from app.common.errors import DuplicateResourceError, NotFoundError
from app.database import get_db
from app.entity import Product
from app.repo import merchants_repo, products_repo
from app.schemas.product import (
    ProductCreateIn,
    ProductListOut,
    ProductOut,
    ProductStatusIn,
    ProductUpdateIn,
)


class ProductService:
    """商品服务"""

    async def get_products_by_merchant(
        self,
        user_id: str,
        *,
        page: int = 1,
        page_size: int = 10,
        keyword: str | None = None,
        status: str | None = None,
    ) -> ProductListOut:
        """获取商家的商品列表"""
        async with get_db() as session:
            merchant = await merchants_repo.get_by_user_id(session, user_id)
            if not merchant:
                raise NotFoundError(MERCHANT_NOT_FOUND)

            products, total = await products_repo.get_list_by_merchant(
                session,
                str(merchant.id),
                page=page,
                page_size=page_size,
                keyword=keyword,
                status=status,
            )

            return ProductListOut(
                items=[ProductOut.model_validate(p) for p in products],
                total=total,
                page=page,
                page_size=page_size,
            )

    async def get_product(self, user_id: str, product_id: str) -> ProductOut:
        """获取商品详情（商家视角，需验证归属）"""
        async with get_db() as session:
            merchant = await merchants_repo.get_by_user_id(session, user_id)
            if not merchant:
                raise NotFoundError(MERCHANT_NOT_FOUND)

            product = await products_repo.get_by_id_and_merchant(
                session, product_id, str(merchant.id)
            )
            if not product:
                raise NotFoundError(PRODUCT_NOT_FOUND)

            return ProductOut.model_validate(product)

    async def get_product_public(self, product_id: str) -> ProductOut:
        """获取商品详情（公开视角，只返回上架商品）"""
        async with get_db() as session:
            product = await products_repo.get_by_id(session, product_id)
            if not product or product.status != "on":
                raise NotFoundError(PRODUCT_NOT_FOUND)

            return ProductOut.model_validate(product)

    async def create_product(
        self, user_id: str, payload: ProductCreateIn
    ) -> ProductOut:
        """创建商品"""
        async with get_db() as session:
            merchant = await merchants_repo.get_by_user_id(session, user_id)
            if not merchant:
                raise NotFoundError(MERCHANT_NOT_FOUND)

            # 检查 SKU 唯一性
            if payload.sku:
                if await products_repo.exists_by_sku(session, payload.sku):
                    raise DuplicateResourceError(PRODUCT_SKU_EXISTS)

            # 创建商品
            product = Product(
                merchant_id=merchant.id,
                name=payload.name,
                sku=payload.sku,
                description=payload.description,
                price=payload.price,
                stock=payload.stock,
                status="on",
            )
            await products_repo.create(session, product)

            # 设置分类关联
            if payload.category_ids:
                await products_repo.set_categories(
                    session, product.id, payload.category_ids
                )

            return ProductOut.model_validate(product)

    async def update_product(
        self, user_id: str, product_id: str, payload: ProductUpdateIn
    ) -> ProductOut:
        """更新商品"""
        async with get_db() as session:
            merchant = await merchants_repo.get_by_user_id(session, user_id)
            if not merchant:
                raise NotFoundError(MERCHANT_NOT_FOUND)

            product = await products_repo.get_by_id_and_merchant(
                session, product_id, str(merchant.id)
            )
            if not product:
                raise NotFoundError(PRODUCT_NOT_FOUND)

            # 检查 SKU 唯一性（排除当前商品）
            update_data = payload.model_dump(exclude_unset=True)
            if "sku" in update_data and update_data["sku"]:
                if await products_repo.exists_by_sku(
                    session, update_data["sku"], exclude_id=product_id
                ):
                    raise NotFoundError(PRODUCT_SKU_EXISTS)

            # 提取分类 ID
            category_ids = update_data.pop("category_ids", None)

            # 更新商品字段
            for key, value in update_data.items():
                setattr(product, key, value)

            await products_repo.update(session, product)

            # 更新分类关联
            if category_ids is not None:
                await products_repo.set_categories(session, product.id, category_ids)

            return ProductOut.model_validate(product)

    async def update_product_status(
        self, user_id: str, product_id: str, payload: ProductStatusIn
    ) -> ProductOut:
        """更新商品上下架状态"""
        async with get_db() as session:
            merchant = await merchants_repo.get_by_user_id(session, user_id)
            if not merchant:
                raise NotFoundError(MERCHANT_NOT_FOUND)

            product = await products_repo.get_by_id_and_merchant(
                session, product_id, str(merchant.id)
            )
            if not product:
                raise NotFoundError(PRODUCT_NOT_FOUND)

            product.status = payload.status
            await products_repo.update(session, product)

            return ProductOut.model_validate(product)
