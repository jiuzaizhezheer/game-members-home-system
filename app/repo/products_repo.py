"""商品仓储层：商品数据访问"""

import uuid

from sqlalchemy import delete as sa_delete
from sqlalchemy import exists, func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entity.pgsql import Merchant, Product, ProductCategory


async def get_by_id(session: AsyncSession, product_id: str) -> Product | None:
    """根据ID获取商品"""
    stmt = select(Product).where(Product.id == product_id)
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_by_id_and_merchant(
    session: AsyncSession, product_id: str, merchant_id: str
) -> Product | None:
    """根据ID和商家ID获取商品（确保商品属于该商家）"""
    stmt = select(Product).where(
        Product.id == product_id,
        Product.merchant_id == merchant_id,
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_list_by_merchant(
    session: AsyncSession,
    merchant_id: str,
    *,
    page: int = 1,
    page_size: int = 10,
    keyword: str | None = None,
    status: str | None = None,
) -> tuple[list[Product], int]:
    """获取商家的商品列表（分页）"""
    # 基础查询
    base_stmt = select(Product).where(Product.merchant_id == merchant_id)

    # 关键字搜索
    if keyword:
        base_stmt = base_stmt.where(Product.name.ilike(f"%{keyword}%"))

    # 状态筛选
    if status:
        base_stmt = base_stmt.where(Product.status == status)

    # 获取总数
    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = (await session.execute(count_stmt)).scalar() or 0

    # 分页查询
    offset = (page - 1) * page_size
    list_stmt = (
        base_stmt.order_by(Product.created_at.desc()).offset(offset).limit(page_size)
    )
    result = await session.execute(list_stmt)
    products = list(result.scalars().all())

    return products, total


async def get_public_list(
    session: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    category_id: str | None = None,
    sort_by: str = "newest",
) -> tuple[list[tuple[Product, uuid.UUID]], int]:
    """获取公开商品列表（仅上架商品）- 返回 (Product, merchant_user_id)"""
    base_stmt = (
        select(Product, Merchant.user_id)
        .join(Merchant, Product.merchant_id == Merchant.id)
        .where(Product.status == "on")
    )

    if keyword:
        # 支持名称或描述搜索
        base_stmt = base_stmt.where(
            (Product.name.ilike(f"%{keyword}%"))
            | (Product.description.ilike(f"%{keyword}%"))
        )

    if category_id:
        # 通过子查询筛选分类
        base_stmt = base_stmt.where(
            Product.id.in_(
                select(ProductCategory.product_id).where(
                    ProductCategory.category_id == category_id
                )
            )
        )

    # 排序逻辑
    if sort_by == "price_asc":
        base_stmt = base_stmt.order_by(Product.price.asc())
    elif sort_by == "price_desc":
        base_stmt = base_stmt.order_by(Product.price.desc())
    elif sort_by == "popularity_desc":
        base_stmt = base_stmt.order_by(
            Product.popularity_score.desc(),
            Product.sales_count.desc(),
            Product.views_count.desc(),
            Product.created_at.desc(),
        )
    else:  # newest
        base_stmt = base_stmt.order_by(Product.created_at.desc())

    # 获取总数
    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = (await session.execute(count_stmt)).scalar() or 0

    # 分页
    offset = (page - 1) * page_size
    list_stmt = base_stmt.offset(offset).limit(page_size)
    result = await session.execute(list_stmt)
    products = list(result.tuples().all())

    return products, total


async def create(session: AsyncSession, product: Product) -> None:
    """创建商品"""
    session.add(product)
    await session.flush()


async def update(session: AsyncSession, product: Product) -> None:
    """更新商品"""
    await session.flush()


async def delete(session: AsyncSession, product: Product) -> None:
    """删除商品"""
    await session.delete(product)
    await session.flush()


async def exists_by_sku(
    session: AsyncSession, sku: str, exclude_id: str | None = None
) -> bool:
    """检查SKU是否已存在"""
    stmt = exists().where(Product.sku == sku)
    if exclude_id:
        stmt = stmt.where(Product.id != exclude_id)
    result = (await session.execute(select(stmt))).scalar()
    return bool(result)


async def set_categories(
    session: AsyncSession, product_id: uuid.UUID, category_ids: list[uuid.UUID]
) -> None:
    """设置商品分类关联"""
    # 先删除现有关联
    await session.execute(
        sa_delete(ProductCategory).where(ProductCategory.product_id == product_id)
    )

    # 添加新关联
    if category_ids:
        await session.execute(
            insert(ProductCategory).values(
                [{"product_id": product_id, "category_id": cid} for cid in category_ids]
            )
        )
    await session.flush()


async def get_categories(
    session: AsyncSession, product_id: str | uuid.UUID
) -> list[uuid.UUID]:
    """获取商品的分类ID列表"""
    stmt = select(ProductCategory.category_id).where(
        ProductCategory.product_id == product_id
    )
    result = await session.execute(stmt)
    return [row[0] for row in result.all()]


async def get_with_merchant_user(
    session: AsyncSession, product_id: str
) -> tuple[Product, uuid.UUID] | None:
    """获取商品及商家用户ID"""
    stmt = (
        select(Product, Merchant.user_id)
        .join(Merchant, Product.merchant_id == Merchant.id)
        .where(Product.id == product_id)
    )
    result = await session.execute(stmt)
    return result.first()  # type: ignore


async def deduct_stock(
    session: AsyncSession, product_id: uuid.UUID, quantity: int
) -> bool:
    """扣减库存 (返回是否成功)"""
    # 使用悲观锁 (SELECT FOR UPDATE) 防止超卖
    stmt = select(Product).where(Product.id == product_id).with_for_update()
    product = (await session.execute(stmt)).scalar_one_or_none()

    if not product or product.stock < quantity:
        return False

    product.stock -= quantity
    await session.flush()
    return True


async def recover_stock(
    session: AsyncSession, product_id: uuid.UUID, quantity: int
) -> None:
    """恢复库存 (异常回滚或取消订单时使用)"""
    stmt = select(Product).where(Product.id == product_id).with_for_update()
    product = (await session.execute(stmt)).scalar_one_or_none()

    if product:
        product.stock += quantity
        await session.flush()


async def increment_views(session: AsyncSession, product_id: uuid.UUID | str) -> None:
    """增加浏览量并更新人气分"""
    stmt = select(Product).where(Product.id == product_id).with_for_update()
    product = (await session.execute(stmt)).scalar_one_or_none()
    if product:
        product.views_count += 1
        # 人气分计算公式：销量*10 + 收藏*5 + 点赞*2 + 浏览*1
        product.popularity_score = (
            (product.sales_count * 10)
            + (product.favorites_count * 5)
            + (product.likes_count * 2)
            + (product.views_count * 1)
        )
        await session.flush()


async def increment_sales(
    session: AsyncSession, product_id: uuid.UUID | str, quantity: int
) -> None:
    """增加销量并更新人气分"""
    stmt = select(Product).where(Product.id == product_id).with_for_update()
    product = (await session.execute(stmt)).scalar_one_or_none()
    if product:
        product.sales_count += quantity
        product.popularity_score = (
            (product.sales_count * 10)
            + (product.favorites_count * 5)
            + (product.likes_count * 2)
            + (product.views_count * 1)
        )
        await session.flush()


async def change_favorites_count(
    session: AsyncSession, product_id: uuid.UUID | str, delta: int
) -> None:
    """更新收藏数并同步人气分"""
    stmt = select(Product).where(Product.id == product_id).with_for_update()
    product = (await session.execute(stmt)).scalar_one_or_none()
    if product:
        product.favorites_count = max(0, product.favorites_count + delta)
        product.popularity_score = (
            (product.sales_count * 10)
            + (product.favorites_count * 5)
            + (product.likes_count * 2)
            + (product.views_count * 1)
        )
        await session.flush()


async def change_likes_count(
    session: AsyncSession, product_id: uuid.UUID | str, delta: int
) -> None:
    """更新点赞数并同步人气分"""
    stmt = select(Product).where(Product.id == product_id).with_for_update()
    product = (await session.execute(stmt)).scalar_one_or_none()
    if product:
        product.likes_count = max(0, product.likes_count + delta)
        product.popularity_score = (
            (product.sales_count * 10)
            + (product.favorites_count * 5)
            + (product.likes_count * 2)
            + (product.views_count * 1)
        )
        await session.flush()
