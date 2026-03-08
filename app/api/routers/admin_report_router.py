from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query, status

from app.api.deps import get_current_user_id, get_report_service
from app.api.role import require_admin
from app.schemas import SuccessResponse
from app.schemas.report import AdminReportDetailOut, AdminReportListOut, ReportHandleIn
from app.services.report_service import ReportService

admin_report_router = APIRouter()


@admin_report_router.get(
    path="/",
    dependencies=[require_admin],
    response_model=SuccessResponse[AdminReportListOut],
    status_code=status.HTTP_200_OK,
)
async def get_report_list(
    report_service: Annotated[ReportService, Depends(get_report_service)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status_: Annotated[str | None, Query(alias="status")] = None,
    target_type: Annotated[str | None, Query()] = None,
) -> SuccessResponse[AdminReportListOut]:
    data = await report_service.get_admin_reports(
        page=page, page_size=page_size, status=status_, target_type=target_type
    )
    return SuccessResponse[AdminReportListOut](message="获取成功", data=data)


@admin_report_router.get(
    path="/{report_id}",
    dependencies=[require_admin],
    response_model=SuccessResponse[AdminReportDetailOut],
    status_code=status.HTTP_200_OK,
)
async def get_report_detail(
    report_id: Annotated[str, Path(description="举报ID")],
    report_service: Annotated[ReportService, Depends(get_report_service)],
) -> SuccessResponse[AdminReportDetailOut]:
    data = await report_service.get_admin_report_detail(report_id)
    return SuccessResponse[AdminReportDetailOut](message="获取成功", data=data)


@admin_report_router.patch(
    path="/{report_id}",
    dependencies=[require_admin],
    response_model=SuccessResponse[bool],
    status_code=status.HTTP_200_OK,
)
async def handle_report(
    report_id: Annotated[str, Path(description="举报ID")],
    user_id: Annotated[str, Depends(get_current_user_id)],
    report_service: Annotated[ReportService, Depends(get_report_service)],
    payload: Annotated[ReportHandleIn, Body(description="处理举报")],
) -> SuccessResponse[bool]:
    await report_service.handle_report(user_id, report_id, payload)
    return SuccessResponse[bool](message="处理成功", data=True)
