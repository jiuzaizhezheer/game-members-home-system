import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.entity.pgsql import User, UserReport


async def create(session: AsyncSession, report: UserReport) -> UserReport:
    session.add(report)
    await session.flush()
    await session.refresh(report)
    return report


async def get_by_id(session: AsyncSession, report_id: uuid.UUID) -> UserReport | None:
    stmt = select(UserReport).where(UserReport.id == report_id)
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_list_my(
    session: AsyncSession,
    reporter_id: uuid.UUID,
    *,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[Sequence[UserReport], int]:
    base = select(UserReport).where(UserReport.reporter_id == reporter_id)
    if status:
        base = base.where(UserReport.status == status)

    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await session.execute(count_stmt)).scalar() or 0

    stmt = (
        base.order_by(desc(UserReport.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await session.execute(stmt)
    return result.scalars().all(), total


async def get_list_admin(
    session: AsyncSession,
    *,
    status: str | None = None,
    target_type: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[Sequence[tuple[UserReport, User]], int]:
    base = (
        select(UserReport, User)
        .join(User, User.id == UserReport.reporter_id)
        .order_by(desc(UserReport.created_at))
    )

    if status:
        base = base.where(UserReport.status == status)
    if target_type:
        base = base.where(UserReport.target_type == target_type)

    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await session.execute(count_stmt)).scalar() or 0

    stmt = base.offset((page - 1) * page_size).limit(page_size)
    rows = (await session.execute(stmt)).tuples().all()
    return rows, total


async def handle(
    session: AsyncSession,
    *,
    report_id: uuid.UUID,
    status: str,
    result: str | None,
    handled_by: uuid.UUID,
    handled_note: str | None,
    handled_at: datetime,
) -> UserReport | None:
    stmt = (
        update(UserReport)
        .where(UserReport.id == report_id)
        .values(
            status=status,
            result=result,
            handled_by=handled_by,
            handled_note=handled_note,
            handled_at=handled_at,
            updated_at=handled_at,
        )
        .returning(UserReport)
    )
    return (await session.execute(stmt)).scalar_one_or_none()
