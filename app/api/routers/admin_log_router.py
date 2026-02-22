"""
管理员 — 操作日志路由
"""

from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.role import require_admin
from app.common.constants import GET_SUCCESS
from app.database.pgsql import get_pg
from app.repo import admin_log_repo
from app.schemas import SuccessResponse
from app.schemas.admin import AdminLogItemOut, AdminLogListOut

admin_log_router = APIRouter()


@admin_log_router.get(
    path="/",
    dependencies=[require_admin],
    response_model=SuccessResponse[AdminLogListOut],
    status_code=status.HTTP_200_OK,
)
async def get_log_list(
    page: Annotated[int, Query(ge=1, description="页码")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="每页数量")] = 20,
) -> SuccessResponse[AdminLogListOut]:
    """管理员查看操作日志列表"""
    async with get_pg() as session:
        logs, total = await admin_log_repo.get_log_list(
            session, page=page, page_size=page_size
        )
        items = [AdminLogItemOut.model_validate(log) for log in logs]
        data = AdminLogListOut(items=items, total=total, page=page, page_size=page_size)
    return SuccessResponse[AdminLogListOut](message=GET_SUCCESS, data=data)
