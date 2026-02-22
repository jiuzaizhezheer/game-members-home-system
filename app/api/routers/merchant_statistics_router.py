from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_current_user_id
from app.api.role import require_merchant
from app.common.constants import GET_SUCCESS
from app.schemas import SuccessResponse
from app.schemas.statistics import (
    DashboardOverviewOut,
    ProductRankingOut,
    SalesTrendOut,
)
from app.services.statistics_service import StatisticsService

merchant_statistics_router = APIRouter()


@merchant_statistics_router.get(
    "/dashboard",
    dependencies=[require_merchant],
    response_model=SuccessResponse[DashboardOverviewOut],
    status_code=status.HTTP_200_OK,
    summary="获取仪表盘概况",
)
async def get_dashboard_overview(
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> SuccessResponse[DashboardOverviewOut]:
    """获取商家控制台总销售额、订单数、商品数等概况"""
    statistics_service = StatisticsService()
    data = await statistics_service.get_dashboard_overview(user_id)
    return SuccessResponse[DashboardOverviewOut](message=GET_SUCCESS, data=data)


@merchant_statistics_router.get(
    "/sales-trend",
    dependencies=[require_merchant],
    response_model=SuccessResponse[SalesTrendOut],
    status_code=status.HTTP_200_OK,
    summary="获取销量趋势",
)
async def get_sales_trend(
    user_id: Annotated[str, Depends(get_current_user_id)],
    days: int = Query(30, description="获取天数"),
) -> SuccessResponse[SalesTrendOut]:
    """获取最近 N 天的销量和订单数趋势"""
    statistics_service = StatisticsService()
    data = await statistics_service.get_sales_trend(user_id, days)
    return SuccessResponse[SalesTrendOut](message=GET_SUCCESS, data=data)


@merchant_statistics_router.get(
    "/top-products",
    dependencies=[require_merchant],
    response_model=SuccessResponse[ProductRankingOut],
    status_code=status.HTTP_200_OK,
    summary="获取商品销量排行",
)
async def get_top_products(
    user_id: Annotated[str, Depends(get_current_user_id)],
    limit: int = Query(5, description="限制条数"),
) -> SuccessResponse[ProductRankingOut]:
    """获取销量前 N 的商品排行"""
    statistics_service = StatisticsService()
    data = await statistics_service.get_top_products(user_id, limit)
    return SuccessResponse[ProductRankingOut](message=GET_SUCCESS, data=data)
