import uuid
from datetime import UTC, datetime

from beanie import PydanticObjectId
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.errors import (
    BusinessError,
    DuplicateResourceError,
    NotFoundError,
    ValidationError,
)
from app.database.pgsql import get_pg
from app.entity.mongodb.comments import Comment
from app.entity.pgsql import User, UserReport
from app.repo import (
    admin_community_repo,
    admin_log_repo,
    admin_products_repo,
    community_repo,
    products_repo,
    reports_repo,
)
from app.schemas.report import (
    AdminReportDetailOut,
    AdminReportItemOut,
    AdminReportListOut,
    ReportCreateIn,
    ReportHandleIn,
    ReportItemOut,
    ReportListOut,
)
from app.services.notification_service import notification_service


class ReportService:
    async def create_report(
        self, user_id: str, payload: ReportCreateIn
    ) -> ReportItemOut:
        await self._ensure_target_exists(payload.target_type, payload.target_id)

        report = UserReport(
            reporter_id=uuid.UUID(user_id),
            target_type=payload.target_type,
            target_id=payload.target_id,
            reason=payload.reason,
            description=payload.description,
            evidence_urls=payload.evidence_urls,
        )

        async with get_pg() as session:
            try:
                await reports_repo.create(session, report)
                await session.commit()
                return ReportItemOut.model_validate(report)
            except IntegrityError as e:
                await session.rollback()
                raise DuplicateResourceError("该内容已举报，请等待处理") from e

    async def get_my_reports(
        self,
        user_id: str,
        *,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
    ) -> ReportListOut:
        async with get_pg() as session:
            items, total = await reports_repo.get_list_my(
                session,
                uuid.UUID(user_id),
                status=status,
                page=page,
                page_size=page_size,
            )
            return ReportListOut(
                items=[ReportItemOut.model_validate(i) for i in items],
                total=total,
                page=page,
                page_size=page_size,
            )

    async def get_admin_reports(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
        target_type: str | None = None,
    ) -> AdminReportListOut:
        async with get_pg() as session:
            rows, total = await reports_repo.get_list_admin(
                session,
                status=status,
                target_type=target_type,
                page=page,
                page_size=page_size,
            )

            items: list[AdminReportItemOut] = []
            for report, reporter in rows:
                base = ReportItemOut.model_validate(report).model_dump()
                items.append(
                    AdminReportItemOut(
                        **base,
                        reporter_name=reporter.username,
                        reporter_avatar_url=reporter.avatar_url,
                    )
                )

            return AdminReportListOut(
                items=items, total=total, page=page, page_size=page_size
            )

    async def get_admin_report_detail(self, report_id: str) -> AdminReportDetailOut:
        rid = uuid.UUID(report_id)
        async with get_pg() as session:
            report = await reports_repo.get_by_id(session, rid)
            if not report:
                raise NotFoundError("举报不存在")
            reporter = await session.get(User, report.reporter_id)
            if not reporter:
                raise NotFoundError("举报人不存在")

            base = ReportItemOut.model_validate(report).model_dump()
            item = AdminReportItemOut(
                **base,
                reporter_name=reporter.username,
                reporter_avatar_url=reporter.avatar_url,
            )

        target_preview = await self._build_target_preview(
            report.target_type, report.target_id
        )
        return AdminReportDetailOut(report=item, target_preview=target_preview)

    async def handle_report(
        self, admin_id: str, report_id: str, payload: ReportHandleIn
    ) -> None:
        rid = uuid.UUID(report_id)
        aid = uuid.UUID(admin_id)
        now = datetime.now(UTC)

        async with get_pg() as session:
            report = await reports_repo.get_by_id(session, rid)
            if not report:
                raise NotFoundError("举报不存在")
            if report.status != "pending":
                raise BusinessError("该举报已处理")

            action_applied = False
            if payload.result == "success":
                action_applied = await self._apply_take_down_action(
                    session, target_type=report.target_type, target_id=report.target_id
                )

            updated = await reports_repo.handle(
                session,
                report_id=rid,
                status="handled",
                result=payload.result,
                handled_by=aid,
                handled_note=payload.handled_note,
                handled_at=now,
            )
            if not updated:
                raise NotFoundError("举报不存在")

            await admin_log_repo.create_log(
                session,
                admin_id=aid,
                action="handle_report",
                target_type="report",
                target_id=str(rid),
                detail={
                    "status": "handled",
                    "result": payload.result,
                    "action_applied": action_applied,
                    "target_type": report.target_type,
                    "target_id": report.target_id,
                },
            )
            await session.commit()

        if payload.result == "success":
            notify_content = "你提交的举报已处理：举报成立，目标内容已下架/移除"
        else:
            notify_content = "你提交的举报已处理：举报不成立，未对目标内容进行处理"

        await notification_service.create_notification(
            str(report.reporter_id),
            "system",
            "举报已处理",
            notify_content,
            None,
        )

    async def _apply_take_down_action(
        self, session: AsyncSession, *, target_type: str, target_id: str
    ) -> bool:
        if target_type == "post":
            try:
                pid = uuid.UUID(target_id)
            except Exception as e:
                raise ValidationError("帖子ID格式不正确") from e
            result = await community_repo.toggle_hide_post(session, pid, True)
            if not result:
                raise NotFoundError("帖子不存在")
            return True

        if target_type == "product":
            product = await admin_products_repo.get_product_by_id(session, target_id)
            if not product:
                raise NotFoundError("商品不存在")
            await admin_products_repo.force_offline_product(session, target_id)
            return True

        if target_type == "comment":
            deleted = await admin_community_repo.delete_comment(target_id)
            if not deleted:
                raise NotFoundError("评论不存在")
            post_id, deleted_count = deleted
            await community_repo.change_comment_count(session, post_id, -deleted_count)
            return True

        raise ValidationError("不支持的举报目标类型")

    async def _ensure_target_exists(self, target_type: str, target_id: str) -> None:
        if target_type == "post":
            try:
                pid = uuid.UUID(target_id)
            except Exception as e:
                raise ValidationError("帖子ID格式不正确") from e
            async with get_pg() as session:
                found = await community_repo.get_post_detail(session, pid)
                if not found:
                    raise NotFoundError("帖子不存在")
            return

        if target_type == "product":
            try:
                uuid.UUID(target_id)
            except Exception as e:
                raise ValidationError("商品ID格式不正确") from e
            async with get_pg() as session:
                product = await products_repo.get_by_id(session, target_id)
                if not product:
                    raise NotFoundError("商品不存在")
            return

        if target_type == "comment":
            try:
                cid = PydanticObjectId(target_id)
            except Exception as e:
                raise ValidationError("评论ID格式不正确") from e
            comment = await Comment.get(cid)
            if not comment:
                raise NotFoundError("评论不存在")
            return

        raise ValidationError("不支持的举报目标类型")

    async def _build_target_preview(
        self, target_type: str, target_id: str
    ) -> str | None:
        if target_type == "post":
            try:
                pid = uuid.UUID(target_id)
            except Exception:
                return None
            async with get_pg() as session:
                row = await community_repo.get_post_detail(session, pid)
                if not row:
                    return None
                post = row[0]
                return post.title

        if target_type == "product":
            async with get_pg() as session:
                product = await products_repo.get_by_id(session, target_id)
                if not product:
                    return None
                return product.name

        if target_type == "comment":
            try:
                cid = PydanticObjectId(target_id)
            except Exception:
                return None
            comment = await Comment.get(cid)
            if not comment:
                return None
            return comment.content[:80]

        return None


report_service = ReportService()
