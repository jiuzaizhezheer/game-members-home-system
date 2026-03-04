import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entity.pgsql import OrderRefund


class OrderRefundsRepo:
    async def create(self, session: AsyncSession, refund: OrderRefund) -> OrderRefund:
        session.add(refund)
        await session.flush()
        return refund

    async def get_by_id(
        self, session: AsyncSession, refund_id: str
    ) -> OrderRefund | None:
        stmt = select(OrderRefund).where(OrderRefund.id == uuid.UUID(refund_id))
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_order_id(
        self, session: AsyncSession, order_id: str
    ) -> OrderRefund | None:
        stmt = (
            select(OrderRefund)
            .where(OrderRefund.order_id == uuid.UUID(order_id))
            .order_by(OrderRefund.created_at.desc())
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_list_by_merchant(
        self,
        session: AsyncSession,
        merchant_id: str,
        page: int,
        page_size: int,
        status: str | None = None,
    ) -> tuple[list[OrderRefund], int]:
        from sqlalchemy import func

        from app.entity.pgsql import Order, OrderItem, Product

        stmt = (
            select(OrderRefund)
            .join(Order, OrderRefund.order_id == Order.id)
            .join(OrderItem, Order.id == OrderItem.order_id)
            .join(Product, OrderItem.product_id == Product.id)
            .where(Product.merchant_id == uuid.UUID(merchant_id))
        )

        if status:
            stmt = stmt.where(OrderRefund.status == status)

        # Distinct is needed because multiple order items might map to the same order refund
        stmt = stmt.distinct(OrderRefund.created_at, OrderRefund.id)

        count_stmt = select(func.count(func.distinct(OrderRefund.id))).select_from(
            stmt.subquery()
        )
        total = await session.scalar(count_stmt)

        stmt = (
            stmt.order_by(OrderRefund.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await session.execute(stmt)
        return list(result.scalars().all()), total or 0


order_refunds_repo = OrderRefundsRepo()
