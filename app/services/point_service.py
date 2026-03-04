import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.constants import MEMBERSHIP_THRESHOLDS
from app.entity.pgsql.point_logs import PointLog
from app.repo import point_logs_repo, users_repo


class PointService:
    """会员积分与成长服务"""

    # 抵扣比例：10 积分 = 1 元
    POINTS_TO_CASH_RATIO = 10

    def calculate_points_deduction(
        self, points: Decimal, total_amount: Decimal
    ) -> tuple[Decimal, Decimal]:
        """
        计算积分可抵扣金额
        规则：
        1. 10 积分 = 1 元
        2. 订单金额满 10 元方可使用
        3. 单笔订单最多抵扣订单总额（优惠后）的 50%
        返回: (抵扣金额, 消耗积分)
        """
        if total_amount < Decimal("10.0"):
            return Decimal("0.0"), Decimal("0.0")

        # 最大可抵扣金额 (50%)
        max_deduction = (total_amount * Decimal("0.5")).quantize(Decimal("0.01"))

        # 现有积分可抵扣金额
        available_deduction = (
            points / Decimal(str(self.POINTS_TO_CASH_RATIO))
        ).quantize(Decimal("0.01"))

        actual_deduction = min(max_deduction, available_deduction)
        actual_points = actual_deduction * Decimal(str(self.POINTS_TO_CASH_RATIO))

        return actual_deduction, actual_points

    async def consume_points(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        points: Decimal,
        reason: str,
        related_id: str | None = None,
        allow_negative: bool = False,
    ) -> None:
        """扣减积分并记录日志"""
        user = await users_repo.get_by_id(session, str(user_id))
        if not user or user.role != "member":
            return

        if user.points < points and not allow_negative:
            from app.common.errors import BusinessError

            raise BusinessError("积分余额不足")

        user.points -= points

        log = PointLog(
            user_id=user_id,
            change_amount=-points,  # 负数表示扣减
            balance_after=user.points,
            reason=reason,
            related_id=related_id,
        )
        await point_logs_repo.add_log(session, log)

    async def grant_points(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        amount: Decimal,
        reason: str,
        related_id: str | None = None,
    ) -> None:
        """发放积分并记录日志"""
        user = await users_repo.get_by_id(session, str(user_id))
        if not user or user.role != "member":
            return

        user.points += amount

        log = PointLog(
            user_id=user_id,
            change_amount=amount,
            balance_after=user.points,
            reason=reason,
            related_id=related_id,
        )
        await point_logs_repo.add_log(session, log)

    async def update_growth(
        self, session: AsyncSession, user_id: uuid.UUID, amount: Decimal
    ) -> None:
        """更新会员成长值 (累计消费) 并尝试晋升等级"""
        user = await users_repo.get_by_id(session, str(user_id))
        if not user or user.role != "member":
            return

        user.total_spent += amount
        # 累计消费金额不能为负数
        user.total_spent = max(user.total_spent, Decimal("0"))

        # 等级晋升逻辑
        spent = user.total_spent
        new_level = "bronze"

        # 从高到低匹配等级
        # 将 MEMBERSHIP_THRESHOLDS 按金额从大到小排序
        sorted_thresholds = sorted(
            MEMBERSHIP_THRESHOLDS.items(), key=lambda x: x[1], reverse=True
        )

        for level_key, threshold in sorted_thresholds:
            if spent >= Decimal(str(threshold)):
                new_level = level_key
                break

        if new_level != user.level:
            user.level = new_level

    async def get_history(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[PointLog], int]:
        """获取积分变动历史记录"""
        return await point_logs_repo.get_by_user_id(session, user_id, page, page_size)


point_service = PointService()
