import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import Date, cast, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entity.pgsql import Order, OrderItem, Product


async def get_dashboard_overview(
    session: AsyncSession, merchant_id: str | uuid.UUID
) -> dict[str, Any]:
    """获取仪表盘概览数据 (不包含 cancelled 订单)"""
    # 基础查询: 关联 order_items, orders, products
    # 筛选条件: product.merchant_id == merchant_id, order.status != 'cancelled'

    # 1. 计算总销售额 & 总订单数 (属于该商家的)
    stmt_total = (
        select(
            func.sum(OrderItem.unit_price * OrderItem.quantity).label("total_sales"),
            func.count(func.distinct(Order.id)).label("order_count"),
        )
        .select_from(OrderItem)
        .join(Order, Order.id == OrderItem.order_id)
        .join(Product, Product.id == OrderItem.product_id)
        .where(Product.merchant_id == merchant_id, Order.status != "cancelled")
    )
    result_total = await session.execute(stmt_total)
    row_total = result_total.first()
    if row_total:
        total_sales = row_total.total_sales or 0
        order_count = row_total.order_count or 0
    else:
        total_sales = 0
        order_count = 0

    # 2. 计算商品总数
    stmt_products = select(func.count(Product.id)).where(
        Product.merchant_id == merchant_id,
        Product.status != "deleted",  # 假设没有逻辑删除，不过以防万一
    )
    product_count = (await session.execute(stmt_products)).scalar() or 0

    # 3. 计算今日销售额
    now = datetime.now(UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    stmt_today = (
        select(func.sum(OrderItem.unit_price * OrderItem.quantity).label("today_sales"))
        .select_from(OrderItem)
        .join(Order, Order.id == OrderItem.order_id)
        .join(Product, Product.id == OrderItem.product_id)
        .where(
            Product.merchant_id == merchant_id,
            Order.status != "cancelled",
            Order.created_at >= today_start,
        )
    )
    today_sales = (await session.execute(stmt_today)).scalar() or 0

    return {
        "total_sales": total_sales,
        "order_count": order_count,
        "product_count": product_count,
        "today_sales": today_sales,
    }


async def get_sales_trend(
    session: AsyncSession, merchant_id: str | uuid.UUID, days: int = 30
) -> list[dict[str, Any]]:
    """获取销量趋势 (按天聚合)"""
    start_date = datetime.now(UTC) - timedelta(days=days)

    # 按天截断日期 (PostgreSQL 使用 DATE_TRUNC 或转换为 date)
    # 为了兼容性，我们可以强制转换 created_at 为 date
    date_expr = cast(Order.created_at, Date).label("date")

    stmt = (
        select(
            date_expr,
            func.sum(OrderItem.unit_price * OrderItem.quantity).label("sales"),
            func.count(func.distinct(Order.id)).label("orders"),
        )
        .select_from(OrderItem)
        .join(Order, Order.id == OrderItem.order_id)
        .join(Product, Product.id == OrderItem.product_id)
        .where(
            Product.merchant_id == merchant_id,
            Order.status != "cancelled",
            Order.created_at >= start_date,
        )
        .group_by(date_expr)
        .order_by(date_expr)
    )

    result = await session.execute(stmt)
    rows = result.all()

    # 填充缺失的日期
    trend_dict = {
        row.date.strftime("%Y-%m-%d"): {
            "sales": row.sales or 0,
            "orders": row.orders or 0,
        }
        for row in rows
        if row.date
    }

    # 生成按天的连续数据
    trend_data = []
    current_date = start_date.date()
    end_date = datetime.now(UTC).date()

    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        data = trend_dict.get(date_str, {"sales": 0, "orders": 0})
        trend_data.append(
            {"date": date_str, "sales": data["sales"], "orders": data["orders"]}
        )
        current_date += timedelta(days=1)

    return trend_data


async def get_top_products(
    session: AsyncSession, merchant_id: str | uuid.UUID, limit: int = 5
) -> list[dict[str, Any]]:
    """获取商品销量排行"""
    stmt = (
        select(
            Product.id,
            Product.name,
            Product.image_url,
            func.sum(OrderItem.unit_price * OrderItem.quantity).label("sales_amount"),
            func.sum(OrderItem.quantity).label("sales_quantity"),
        )
        .select_from(OrderItem)
        .join(Order, Order.id == OrderItem.order_id)
        .join(Product, Product.id == OrderItem.product_id)
        .where(Product.merchant_id == merchant_id, Order.status != "cancelled")
        .group_by(Product.id, Product.name, Product.image_url)
        .order_by(desc("sales_quantity"))
        .limit(limit)
    )

    result = await session.execute(stmt)
    rows = result.all()

    return [
        {
            "product_id": row.id,
            "product_name": row.name,
            "image_url": row.image_url,
            "sales_amount": row.sales_amount or 0,
            "sales_quantity": row.sales_quantity or 0,
        }
        for row in rows
    ]
