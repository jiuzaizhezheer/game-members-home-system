from app.common.errors import BusinessError
from app.database.pgsql import get_pg
from app.repo import merchants_repo, statistics_repo
from app.schemas.statistics import (
    DashboardOverviewOut,
    ProductRankingItem,
    ProductRankingOut,
    SalesTrendItem,
    SalesTrendOut,
)


class StatisticsService:
    """销售数据统计服务"""

    async def get_dashboard_overview(self, user_id: str) -> DashboardOverviewOut:
        """获取商家控制台数据概览"""
        async with get_pg() as session:
            merchant = await merchants_repo.get_by_user_id(session, user_id)
            if not merchant:
                raise BusinessError(detail="当前用户未开通店铺")

            data = await statistics_repo.get_dashboard_overview(session, merchant.id)
            return DashboardOverviewOut.model_validate(data)

    async def get_sales_trend(self, user_id: str, days: int = 30) -> SalesTrendOut:
        """获取最近销量趋势"""
        async with get_pg() as session:
            merchant = await merchants_repo.get_by_user_id(session, user_id)
            if not merchant:
                raise BusinessError(detail="当前用户未开通店铺")

            data = await statistics_repo.get_sales_trend(session, merchant.id, days)
            items = [SalesTrendItem.model_validate(item) for item in data]
            return SalesTrendOut(items=items)

    async def get_top_products(self, user_id: str, limit: int = 5) -> ProductRankingOut:
        """获取商品销量排行"""
        async with get_pg() as session:
            merchant = await merchants_repo.get_by_user_id(session, user_id)
            if not merchant:
                raise BusinessError(detail="当前用户未开通店铺")

            data = await statistics_repo.get_top_products(session, merchant.id, limit)
            items = [ProductRankingItem.model_validate(item) for item in data]
            return ProductRankingOut(items=items)
