from app.common.constants import INVALID_CREDENTIALS, USERNAME_OR_EMAIL_EXISTS
from app.common.errors import DuplicateResourceError, ValidationError
from app.common.utils import is_valid_email
from app.database.session import get_session
from app.entity import User
from app.middleware.security import hash_password, verify_password
from app.model import UserOut
from app.model.auth import LoginRequest, RegisterRequest
from app.repo.users_repo import (
    exists_by_username_or_email,
    get_by_email,
    get_by_username,
    insert,
)


class AuthService:
    async def register_user(self, payload: RegisterRequest) -> UserOut:
        async with get_session() as session:
            if await exists_by_username_or_email(
                session, payload.username, payload.email
            ):
                raise DuplicateResourceError(USERNAME_OR_EMAIL_EXISTS)
            user = User(
                username=payload.username,
                email=payload.email,
                role=payload.role,
                password_hash=hash_password(payload.password),
            )
            await insert(session, user)
            return UserOut(
                id=str(user.id),
                username=user.username,
                email=user.email,
                role=user.role,
                created_at=user.created_at,
            )

    async def login_user(self, payload: LoginRequest) -> UserOut:
        async with get_session() as session:
            # 判断是用户名还是邮箱
            if is_valid_email(payload.username_or_email):
                # 是邮箱
                user = await get_by_email(session, payload.username_or_email)
            else:
                # 是用户名
                user = await get_by_username(session, payload.username_or_email)

            if not user or not verify_password(payload.password, user.password_hash):
                raise ValidationError(INVALID_CREDENTIALS)

            return UserOut(
                id=str(user.id),
                username=user.username,
                email=user.email,
                role=user.role,
                created_at=user.created_at,
            )
