from decimal import Decimal

from app.common.constants import (
    MEMBERSHIP_LEVEL_NAMES,
    MEMBERSHIP_THRESHOLDS,
    NEW_PASSWORD_SAME_AS_OLD,
    OLD_PASSWORD_ERROR,
    USER_NOT_FOUND,
)
from app.common.errors import NotFoundError, ValidationError
from app.database.pgsql import get_pg
from app.entity.pgsql import User
from app.repo import users_repo
from app.schemas import (
    PointLogListOut,
    PointLogOut,
    UserChangePasswordIn,
    UserOut,
    UserProfileUpdateIn,
)
from app.utils import hash_password, verify_password


class UserService:
    async def get_by_id(self, user_id: str) -> User:
        """根据ID获取用户"""
        async with get_pg() as session:
            user = await users_repo.get_by_id(session, user_id)
            if not user:
                raise NotFoundError(USER_NOT_FOUND)
            return user

    async def get_profile(self, user_id: str) -> UserOut:
        """获取用户个人资料"""
        user = await self.get_by_id(user_id)
        user_out = UserOut.model_validate(user)

        # 计算下一等级进度
        total_spent = user.total_spent

        # 找出比当前等级更高的下一个等级
        thresholds = sorted(MEMBERSHIP_THRESHOLDS.items(), key=lambda x: x[1])
        next_level_name = None
        next_level_threshold = None

        for level_key, threshold in thresholds:
            if threshold > total_spent:
                next_level_name = MEMBERSHIP_LEVEL_NAMES.get(level_key)
                next_level_threshold = Decimal(str(threshold))
                break

        user_out.next_level_name = next_level_name
        user_out.next_level_threshold = next_level_threshold

        return user_out

    async def update_profile(
        self, user_id: str, payload: UserProfileUpdateIn
    ) -> UserOut:
        """更新用户个人资料"""
        async with get_pg() as session:
            user = await users_repo.get_by_id(session, user_id)
            if not user:
                raise NotFoundError(USER_NOT_FOUND)

            update_data = payload.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(user, field, value)

            await session.flush()
            return UserOut.model_validate(user)

    async def change_password(
        self, user_id: str, payload: UserChangePasswordIn
    ) -> None:
        """已登录情况下通过旧密码修改用户密码服务"""
        async with get_pg() as session:
            user = await users_repo.get_by_id(session, user_id)
            if not user:
                raise NotFoundError(USER_NOT_FOUND)

            if not verify_password(payload.old_password, user.password_hash):
                raise ValidationError(OLD_PASSWORD_ERROR)

            # 防御性校验：确保新密码与数据库当前密码不同
            if verify_password(payload.new_password, user.password_hash):
                raise ValidationError(NEW_PASSWORD_SAME_AS_OLD)

            new_password_hash = hash_password(payload.new_password)
            await users_repo.update_password_hash(session, user, new_password_hash)

    async def get_point_history(
        self, user_id: str, page: int = 1, page_size: int = 10
    ) -> PointLogListOut:
        """获取用户积分记录"""
        import uuid

        from app.services.point_service import point_service

        async with get_pg() as session:
            logs, total = await point_service.get_history(
                session, uuid.UUID(user_id), page, page_size
            )
            log_items = [PointLogOut.model_validate(log) for log in logs]
            return PointLogListOut(
                items=log_items, total=total, page=page, page_size=page_size
            )
