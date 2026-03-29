import uuid
from datetime import UTC, datetime
from decimal import Decimal

from app.common.errors import BusinessError, NotFoundError
from app.database.pgsql import get_pg
from app.entity.pgsql import Coupon, UserCoupon
from app.repo import coupons_repo
from app.schemas.coupon import (
    CouponCenterOut,
    CouponCreateIn,
    CouponOut,
    CouponUpdateIn,
    UserCouponOut,
)


class CouponService:
    """优惠券服务层"""

    async def create_coupon(
        self, merchant_id: uuid.UUID | None, payload: CouponCreateIn
    ) -> CouponOut:
        """创建优惠券 (商家或平台)"""
        async with get_pg() as session:
            coupon = await coupons_repo.create_coupon(session, merchant_id, payload)
            return CouponOut.model_validate(coupon)

    async def list_claimable_coupons(
        self, user_id: uuid.UUID, page: int = 1, page_size: int = 20
    ) -> tuple[list[CouponCenterOut], int]:
        """领券中心：获取可领取的优惠券列表"""
        async with get_pg() as session:
            # 仅展示 active 状态且在有效期内的
            items, total = await coupons_repo.list_coupons(
                session, is_active_only=True, page=page, page_size=page_size
            )

            # 标记用户是否已领取
            coupon_ids = [item.id for item in items]
            claimed_ids = await coupons_repo.get_claimed_coupon_ids(
                session, user_id, coupon_ids
            )

            out_items = []
            for item in items:
                # 转换
                out = CouponCenterOut.model_validate(item)
                out.is_claimed = item.id in claimed_ids
                out.is_fully_issued = (
                    item.total_quantity > 0 and item.issued_count >= item.total_quantity
                )
                out_items.append(out)

            return out_items, total

    async def list_merchant_coupons(
        self, merchant_id: uuid.UUID | None, page: int = 1, page_size: int = 20
    ) -> tuple[list[CouponOut], int]:
        """商户端：获取商家的优惠券列表"""
        async with get_pg() as session:
            items, total = await coupons_repo.list_coupons(
                session,
                merchant_id=merchant_id,
                is_active_only=False,
                page=page,
                page_size=page_size,
            )
            return [CouponOut.model_validate(item) for item in items], total

    async def claim_coupon(
        self, user_id: uuid.UUID, coupon_id: uuid.UUID
    ) -> UserCouponOut:
        """领取优惠券"""
        async with get_pg() as session:
            # 1. 检查优惠券是否存在及状态
            coupon = await coupons_repo.get_coupon_by_id(session, coupon_id)
            if not coupon:
                raise NotFoundError("优惠券不存在")

            if coupon.status != "active":
                raise BusinessError("优惠券已下架")

            now = datetime.now(UTC)
            if now < coupon.start_at:
                raise BusinessError("领券活动还未开始")
            if now > coupon.end_at:
                raise BusinessError("领券活动已结束")

            # 2. 检查用户是否领过 (暂定每人限领一张同类券)
            existing = await coupons_repo.get_user_coupon(session, user_id, coupon_id)
            if existing:
                raise BusinessError("您已经领取过该优惠券了")

            # 3. 原子性核减并创建记录
            # 使用事务确保一致性
            # 注意：atomic_increment_issued_count 已经在 repo 中实现了总量校验
            success = await coupons_repo.atomic_increment_issued_count(
                session, coupon_id
            )
            if not success:
                raise BusinessError("优惠券已被抢光了")

            # 刷新 coupon 以确保 issued_count 等属性是最新的，且未过期
            await session.refresh(coupon)

            user_coupon = await coupons_repo.create_user_coupon(
                session, user_id, coupon_id
            )
            if not user_coupon:
                raise BusinessError("领取失败")

            # 刷新 user_coupon 以确保自动生成的 ID 和时间戳已加载
            await session.refresh(user_coupon)

            # 手动挂载关联对象，防止 Pydantic 验证时触发异步 Lazy Loading 导致崩溃
            user_coupon.coupon = coupon

            return UserCouponOut.model_validate(user_coupon)

    async def list_my_coupons(
        self,
        user_id: uuid.UUID,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[UserCouponOut], int]:
        """我的券包"""
        async with get_pg() as session:
            items, total = await coupons_repo.list_user_coupons(
                session, user_id, status, page, page_size
            )

            # 我们需要关联 Coupon 详情，repo 中已经处理了懒加载或我们可以手动加载
            # 这里依赖于实体定义的 relationship 或者我们在查询时加入 join (目前 repo 是简易 select)
            # 为了严谨，建议在 repo 中使用 selectinload
            return [UserCouponOut.model_validate(item) for item in items], total

    async def validate_coupon_for_order(
        self,
        user_id: uuid.UUID,
        user_coupon_id: uuid.UUID,
        order_amount: Decimal,
        merchant_ids: set[uuid.UUID] | None = None,
    ) -> tuple[UserCoupon, Coupon]:
        """校验优惠券是否可用于当前订单"""
        async with get_pg() as session:
            user_coupon = await coupons_repo.get_user_coupon_by_id(
                session, user_coupon_id
            )
            if not user_coupon or user_coupon.user_id != user_id:
                raise BusinessError("优惠券无效")

            if user_coupon.status != "unused":
                raise BusinessError("优惠券已被使用或已失效")

            # 手动加载关联的 Coupon (如果还没加载)
            coupon = await coupons_repo.get_coupon_by_id(session, user_coupon.coupon_id)
            if not coupon or coupon.status != "active":
                raise BusinessError("关联的优惠券已下架")

            now = datetime.now(UTC)
            if now > coupon.end_at:
                raise BusinessError("优惠券已过期")

            if order_amount < coupon.min_spend:
                raise BusinessError(f"未达到最低消费门槛 ¥{coupon.min_spend}")

            # 如果是商家券，校验订单中是否包含该商家的商品
            # 如果是官方券 (merchant_id is None)，跳过此校验
            if coupon.merchant_id and merchant_ids is not None:
                if coupon.merchant_id not in merchant_ids:
                    raise BusinessError("该优惠券不适用于此商家")

            return user_coupon, coupon

    async def update_coupon_by_merchant(
        self, merchant_id: uuid.UUID, coupon_id: uuid.UUID, payload: CouponUpdateIn
    ) -> CouponOut:
        """商户端：更新优惠券信息"""
        async with get_pg() as session:
            coupon = await coupons_repo.get_coupon_by_id(session, coupon_id)
            if not coupon:
                raise NotFoundError("优惠券不存在")

            if coupon.merchant_id != merchant_id:
                raise BusinessError("无权操作此优惠券")

            updated = await coupons_repo.update_coupon(session, coupon_id, payload)
            return CouponOut.model_validate(updated)

    async def admin_update_coupon(
        self, coupon_id: uuid.UUID, payload: CouponUpdateIn
    ) -> CouponOut:
        """管理员：强制更新任意优惠券信息"""
        async with get_pg() as session:
            coupon = await coupons_repo.get_coupon_by_id(session, coupon_id)
            if not coupon:
                raise NotFoundError("优惠券不存在")

            updated = await coupons_repo.update_coupon(session, coupon_id, payload)
            return CouponOut.model_validate(updated)
