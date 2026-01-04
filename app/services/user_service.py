from app.common.constants import (
    INVALID_CREDENTIALS,
    OLD_PASSWORD_ERROR,
    USER_NOT_FOUND,
    USERNAME_OR_EMAIL_EXISTS,
)
from app.common.errors import DuplicateResourceError, ValidationError
from app.database.session import get_session
from app.entity import User
from app.model import (
    TokenOut,
    UserChangePasswordRequest,
    UserLoginRequest,
    UserRegisterRequest,
)
from app.repo import users_repo
from app.utils.password_util import hash_password, verify_password
from app.utils.token_util import get_access_token, get_refresh_token
from app.utils.validutil import is_valid_email


class UserService:
    async def register(self, payload: UserRegisterRequest) -> None:
        """用户注册服务"""
        async with get_session() as session:
            if await users_repo.exists_by_username_or_email(
                session, payload.username, payload.email
            ):
                raise DuplicateResourceError(USERNAME_OR_EMAIL_EXISTS)
            user = User(
                username=payload.username,
                email=payload.email,
                role=payload.role,
                password_hash=hash_password(payload.password),
            )
            await users_repo.create(session, user)

    async def login(self, payload: UserLoginRequest) -> TokenOut:
        """用户登录服务"""
        async with get_session() as session:
            # 判断是用户名还是邮箱
            if is_valid_email(payload.username_or_email):
                # 是邮箱
                user = await users_repo.get_by_email(session, payload.username_or_email)
            else:
                # 是用户名
                user = await users_repo.get_by_username(
                    session, payload.username_or_email
                )

            if not user or not verify_password(payload.password, user.password_hash):
                raise ValidationError(INVALID_CREDENTIALS)

            # 生成 access_token
            access_token = get_access_token(str(user.id), user.role)
            # 生成 refresh_token
            refresh_token = await get_refresh_token(str(user.id), user.role)

            return TokenOut(access_token=access_token, refresh_token=refresh_token)

    async def change_password(
        self, user_id: str, payload: UserChangePasswordRequest
    ) -> None:
        """修改用户密码服务"""
        async with get_session() as session:
            user = await users_repo.get_by_id(session, user_id)
            if not user:
                raise ValidationError(USER_NOT_FOUND)

            if not verify_password(payload.old_password, user.password_hash):
                raise ValidationError(OLD_PASSWORD_ERROR)

            new_password_hash = hash_password(payload.new_password)
            await users_repo.update_password_hash(session, user, new_password_hash)
