"""管理员操作日志仓储层"""

import uuid
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entity.pgsql import AdminLog


async def create_log(
    session: AsyncSession,
    *,
    admin_id: uuid.UUID,
    action: str,
    target_type: str,
    target_id: str,
    detail: dict[str, Any] | None = None,
) -> AdminLog:
    """写入一条管理员操作日志"""
    log = AdminLog(
        admin_id=admin_id,
        action=action,
        target_type=target_type,
        target_id=str(target_id),
        detail=detail,
    )
    session.add(log)
    await session.flush()
    return log


async def get_log_list(
    session: AsyncSession,
    *,
    admin_id: uuid.UUID | None = None,
    action: str | None = None,
    target_type: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[AdminLog], int]:
    """分页查询操作日志"""
    from sqlalchemy import func

    base = select(AdminLog)

    if admin_id is not None:
        base = base.where(AdminLog.admin_id == admin_id)
    if action:
        base = base.where(AdminLog.action == action)
    if target_type:
        base = base.where(AdminLog.target_type == target_type)

    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await session.execute(count_stmt)).scalar() or 0

    offset = (page - 1) * page_size
    list_stmt = base.order_by(desc(AdminLog.created_at)).offset(offset).limit(page_size)
    result = await session.execute(list_stmt)
    logs = list(result.scalars().all())

    return logs, total
