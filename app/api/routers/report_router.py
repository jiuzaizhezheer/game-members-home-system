from typing import Annotated

from fastapi import APIRouter, Body, Depends, Query, status

from app.api.deps import get_current_user_id, get_report_service
from app.api.role import require_member_or_merchant
from app.schemas import SuccessResponse
from app.schemas.report import ReportCreateIn, ReportItemOut, ReportListOut
from app.services.report_service import ReportService

report_router = APIRouter()


@report_router.post(
    path="/",
    dependencies=[require_member_or_merchant],
    response_model=SuccessResponse[ReportItemOut],
    status_code=status.HTTP_201_CREATED,
)
async def create_report(
    user_id: Annotated[str, Depends(get_current_user_id)],
    report_service: Annotated[ReportService, Depends(get_report_service)],
    payload: Annotated[ReportCreateIn, Body(description="举报提交")],
) -> SuccessResponse[ReportItemOut]:
    item = await report_service.create_report(user_id, payload)
    return SuccessResponse[ReportItemOut](message="举报提交成功", data=item)


@report_router.get(
    path="/my",
    dependencies=[require_member_or_merchant],
    response_model=SuccessResponse[ReportListOut],
    status_code=status.HTTP_200_OK,
)
async def get_my_reports(
    user_id: Annotated[str, Depends(get_current_user_id)],
    report_service: Annotated[ReportService, Depends(get_report_service)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status_: Annotated[str | None, Query(alias="status")] = None,
) -> SuccessResponse[ReportListOut]:
    data = await report_service.get_my_reports(
        user_id, page=page, page_size=page_size, status=status_
    )
    return SuccessResponse[ReportListOut](message="获取成功", data=data)
