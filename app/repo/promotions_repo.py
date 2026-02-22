import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.entity.pgsql.products import Product
from app.entity.pgsql.promotion_products import PromotionProduct
from app.entity.pgsql.promotions import Promotion


async def get_promotion_by_id(
    session: AsyncSession, promotion_id: uuid.UUID
) -> Promotion | None:
    stmt = select(Promotion).where(Promotion.id == promotion_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_promotion_products(
    session: AsyncSession, promotion_id: uuid.UUID
) -> Sequence[Product]:
    stmt = (
        select(Product)
        .join(PromotionProduct, Product.id == PromotionProduct.product_id)
        .where(PromotionProduct.promotion_id == promotion_id)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def create_promotion(
    session: AsyncSession, promotion: Promotion, product_ids: list[uuid.UUID]
) -> Promotion:
    session.add(promotion)
    await session.flush()
    # Ensure ID is generated
    await session.refresh(promotion)

    if product_ids:
        connections = [
            PromotionProduct(promotion_id=promotion.id, product_id=pid)
            for pid in product_ids
        ]
        session.add_all(connections)

    return promotion


async def update_promotion(
    session: AsyncSession,
    promotion_id: uuid.UUID,
    product_ids: list[uuid.UUID] | None = None,
    **kwargs,
) -> Promotion | None:
    if kwargs:
        stmt = update(Promotion).where(Promotion.id == promotion_id).values(**kwargs)
        await session.execute(stmt)

    if product_ids is not None:
        # Delete existing connections
        await session.execute(
            delete(PromotionProduct).where(
                PromotionProduct.promotion_id == promotion_id
            )
        )
        # Add new connections
        if product_ids:
            connections = [
                PromotionProduct(promotion_id=promotion_id, product_id=pid)
                for pid in product_ids
            ]
            session.add_all(connections)

    return await get_promotion_by_id(session, promotion_id)


async def delete_promotion(session: AsyncSession, promotion_id: uuid.UUID) -> None:
    # Delete connections first (manual cascade)
    await session.execute(
        delete(PromotionProduct).where(PromotionProduct.promotion_id == promotion_id)
    )
    await session.execute(delete(Promotion).where(Promotion.id == promotion_id))


async def get_merchant_promotions(
    session: AsyncSession, merchant_id: uuid.UUID, page: int, page_size: int
) -> tuple[Sequence[Promotion], int]:
    stmt = (
        select(Promotion)
        .where(Promotion.merchant_id == merchant_id)
        .order_by(Promotion.created_at.desc())
    )
    count_stmt = (
        select(func.count())
        .select_from(Promotion)
        .where(Promotion.merchant_id == merchant_id)
    )

    total = await session.scalar(count_stmt)

    result = await session.execute(stmt.offset((page - 1) * page_size).limit(page_size))
    return result.scalars().all(), total or 0


async def get_active_promotions_by_product_ids(
    session: AsyncSession, product_ids: list[uuid.UUID]
) -> Sequence[tuple[uuid.UUID, Promotion]]:
    """获取指定商品的当前有效促销活动"""
    if not product_ids:
        return []

    now = datetime.now()

    stmt = (
        select(PromotionProduct.product_id, Promotion)
        .join(Promotion, Promotion.id == PromotionProduct.promotion_id)
        .where(
            PromotionProduct.product_id.in_(product_ids),
            Promotion.status == "active",
            Promotion.start_at <= now,
            Promotion.end_at >= now,
        )
        # 按照创建时间倒序，确保后续处理时优先取最新的（或在应用层处理优先级）
        .order_by(Promotion.created_at.desc())
    )

    result = await session.execute(stmt)
    return result.tuples().all()
