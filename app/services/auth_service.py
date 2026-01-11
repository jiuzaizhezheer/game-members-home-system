from app.common.constants import (
    INVALID_CREDENTIALS,
    USERNAME_OR_EMAIL_EXISTS,
)
from app.common.errors import DuplicateResourceError, ValidationError
from app.database import get_db
from app.entity import User
from app.repo import users_repo
from app.schemas import AuthLoginIn, AuthRegisterIn, TokenOut
from app.utils import (
    get_access_token,
    get_refresh_token,
    hash_password,
    verify_password,
)


class AuthService:
    async def register(self, payload: AuthRegisterIn) -> None:
        """用户注册服务"""
        async with get_db() as session:
            if await users_repo.exists_by_username_or_email_in_role(
                session, payload.username, payload.email, payload.role
            ):
                raise DuplicateResourceError(USERNAME_OR_EMAIL_EXISTS)
            user = User(
                username=payload.username,
                email=payload.email,
                role=payload.role,
                password_hash=hash_password(payload.password),
            )
            await users_repo.create(session, user)

    async def login(self, payload: AuthLoginIn) -> TokenOut:
        """用户登录服务"""
        async with get_db() as session:
            # 验证邮箱是否存在
            user = await users_repo.get_by_email(session, payload.email, payload.role)

            if not user or not verify_password(payload.password, user.password_hash):
                raise ValidationError(INVALID_CREDENTIALS)
            # 生成access_token 和 refresh_token
            access_token = get_access_token(str(user.id), user.role)
            refresh_token = await get_refresh_token(str(user.id), user.role)

            return TokenOut(access_token=access_token, refresh_token=refresh_token)
