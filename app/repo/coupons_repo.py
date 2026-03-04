import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import cast

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager

from app.entity.pgsql import Coupon, UserCoupon
from app.schemas.coupon import CouponCreateIn, CouponUpdateIn


async def create_coupon(
    session: AsyncSession, merchant_id: uuid.UUID | None, payload: CouponCreateIn
) -> Coupon:
    """创建优惠券"""
    coupon = Coupon(merchant_id=merchant_id, **payload.model_dump())
    session.add(coupon)
    await session.flush()
    return coupon


async def get_coupon_by_id(
    session: AsyncSession, coupon_id: uuid.UUID
) -> Coupon | None:
    """根据ID获取优惠券"""
    stmt = select(Coupon).where(Coupon.id == coupon_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_coupons(
    session: AsyncSession,
    merchant_id: uuid.UUID | None = None,
    is_active_only: bool = True,
    page: int = 1,
    page_size: int = 20,
) -> tuple[Sequence[Coupon], int]:
    """查询优惠券列表"""
    stmt = select(Coupon)

    # 过滤器
    filters = []
    if merchant_id is not None:
        filters.append(Coupon.merchant_id == merchant_id)
    if is_active_only:
        filters.append(Coupon.status == "active")
        now = datetime.now(UTC)
        filters.append(and_(Coupon.start_at <= now, Coupon.end_at >= now))

    if filters:
        stmt = stmt.where(and_(*filters))

    # 总数
    count_stmt = select(func.count()).select_from(stmt.subquery())
    count_result = await session.execute(count_stmt)
    total = count_result.scalar() or 0

    # 分页
    stmt = (
        stmt.order_by(Coupon.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await session.execute(stmt)
    return result.scalars().all(), total


async def update_coupon(
    session: AsyncSession, coupon_id: uuid.UUID, payload: CouponUpdateIn
) -> Coupon | None:
    """更新优惠券信息"""
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        return await get_coupon_by_id(session, coupon_id)

    stmt = (
        update(Coupon)
        .where(Coupon.id == coupon_id)
        .values(**update_data, updated_at=datetime.now(UTC))
    )
    await session.execute(stmt)
    return await get_coupon_by_id(session, coupon_id)


async def get_user_coupon(
    session: AsyncSession, user_id: uuid.UUID, coupon_id: uuid.UUID
) -> UserCoupon | None:
    """检查用户是否已领取过该券"""
    stmt = select(UserCoupon).where(
        and_(UserCoupon.user_id == user_id, UserCoupon.coupon_id == coupon_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_user_coupon(
    session: AsyncSession, user_id: uuid.UUID, coupon_id: uuid.UUID
) -> UserCoupon | None:
    """创建领取记录"""
    # 这里通常需要在原子操作中并发安全地增加 issued_count
    # 逻辑会在 Service 层处理
    user_coupon = UserCoupon(user_id=user_id, coupon_id=coupon_id, status="unused")
    session.add(user_coupon)
    await session.flush()
    return user_coupon


async def list_user_coupons(
    session: AsyncSession,
    user_id: uuid.UUID,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[Sequence[UserCoupon], int]:
    """查询用户券包"""
    now = datetime.now(UTC)
    # 关联 Coupon 详情
    stmt = (
        select(UserCoupon)
        .join(UserCoupon.coupon)
        .options(contains_eager(UserCoupon.coupon))
        .where(UserCoupon.user_id == user_id)
    )

    if status == "unused":
        # 待使用：主表未使用 且 关联表为激活 且 未过期
        stmt = stmt.where(
            UserCoupon.status == "unused",
            Coupon.status == "active",
            Coupon.end_at > now,
        )
    elif status == "inactive":
        # 已下架：主表未使用 且 关联表为停用
        stmt = stmt.where(UserCoupon.status == "unused", Coupon.status == "inactive")
    elif status == "expired":
        # 已过期：主表已过期 OR (主表未使用 且 关联表为激活 且 已过期)
        stmt = stmt.where(
            or_(
                UserCoupon.status == "expired",
                and_(
                    UserCoupon.status == "unused",
                    Coupon.status == "active",
                    Coupon.end_at <= now,
                ),
            )
        )
    elif status == "used":
        stmt = stmt.where(UserCoupon.status == "used")
    elif status:
        stmt = stmt.where(UserCoupon.status == status)

    # 总数
    count_stmt = select(func.count()).select_from(stmt.subquery())
    count_result = await session.execute(count_stmt)
    total = count_result.scalar() or 0

    # 关联分页
    stmt = (
        stmt.order_by(UserCoupon.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await session.execute(stmt)
    return result.scalars().all(), total


async def get_user_coupon_by_id(
    session: AsyncSession, user_coupon_id: uuid.UUID
) -> UserCoupon | None:
    """根据领取记录ID获取"""
    stmt = select(UserCoupon).where(UserCoupon.id == user_coupon_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def use_user_coupon(
    session: AsyncSession, user_coupon_id: uuid.UUID, order_id: uuid.UUID
):
    """核销优惠券"""
    stmt = (
        update(UserCoupon)
        .where(UserCoupon.id == user_coupon_id)
        .values(
            status="used",
            order_id=order_id,
            used_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
    )
    await session.execute(stmt)


async def atomic_increment_issued_count(
    session: AsyncSession, coupon_id: uuid.UUID
) -> bool:
    """原子性增加领券数量并校验总量"""
    stmt = (
        update(Coupon)
        .where(
            and_(
                Coupon.id == coupon_id,
                or_(
                    Coupon.total_quantity == 0,
                    Coupon.issued_count < Coupon.total_quantity,
                ),
            )
        )
        .values(issued_count=Coupon.issued_count + 1)
    )
    result = cast(CursorResult, await session.execute(stmt))
    return result.rowcount > 0
