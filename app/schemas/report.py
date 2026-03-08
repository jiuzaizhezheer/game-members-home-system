import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ReportTargetType = Literal["post", "comment", "product"]
ReportStatus = Literal["pending", "handled"]
ReportResult = Literal["success", "fail"]


class ReportCreateIn(BaseModel):
    target_type: ReportTargetType = Field(description="举报目标类型")
    target_id: str = Field(min_length=1, max_length=64, description="举报目标ID")
    reason: str = Field(min_length=1, max_length=64, description="举报原因")
    description: str | None = Field(
        default=None, max_length=2000, description="补充说明"
    )
    evidence_urls: list[str] = Field(
        default_factory=list, description="证据图片URL列表"
    )


class ReportHandleIn(BaseModel):
    result: ReportResult = Field(
        description="处理结果：success=举报成立并执行下架，fail=举报不成立不处理"
    )
    handled_note: str | None = Field(
        default=None, max_length=255, description="处理备注"
    )


class ReportItemOut(BaseModel):
    id: uuid.UUID
    reporter_id: uuid.UUID
    target_type: ReportTargetType
    target_id: str
    reason: str
    description: str | None = None
    evidence_urls: list[str] = Field(default_factory=list)
    status: ReportStatus
    result: ReportResult | None = None
    handled_by: uuid.UUID | None = None
    handled_note: str | None = None
    handled_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReportListOut(BaseModel):
    items: list[ReportItemOut]
    total: int
    page: int
    page_size: int


class AdminReportItemOut(ReportItemOut):
    reporter_name: str = Field(description="举报人昵称")
    reporter_avatar_url: str | None = Field(default=None, description="举报人头像")


class AdminReportListOut(BaseModel):
    items: list[AdminReportItemOut]
    total: int
    page: int
    page_size: int


class AdminReportDetailOut(BaseModel):
    report: AdminReportItemOut
    target_preview: str | None = Field(default=None, description="目标摘要预览")
