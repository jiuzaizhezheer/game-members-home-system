from app.common.constants import (
    NEW_PASSWORD_SAME_AS_OLD,
    OLD_PASSWORD_ERROR,
    USER_NOT_FOUND,
)
from app.common.errors import NotFoundError, ValidationError
from app.database import get_db
from app.entity import User
from app.repo import users_repo
from app.schemas import UserChangePasswordIn
from app.utils import hash_password, verify_password


class UserService:
    async def get_by_id(self, user_id: str) -> User:
        """根据ID获取用户"""
        async with get_db() as session:
            user = await users_repo.get_by_id(session, user_id)
            if not user:
                raise NotFoundError(USER_NOT_FOUND)
            return user

    async def change_password(
        self, user_id: str, payload: UserChangePasswordIn
    ) -> None:
        """已登录情况下通过旧密码修改用户密码服务"""
        async with get_db() as session:
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
