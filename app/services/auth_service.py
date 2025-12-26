from app.common.constants import USERNAME_OR_EMAIL_EXISTS
from app.common.errors import DuplicateResourceError
from app.database.session import get_session
from app.entity import User
from app.middleware.security import hash_password
from app.model import UserOut
from app.model.auth import RegisterRequest
from app.repo.users_repo import exists_by_username_or_email, insert


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

    # async def login_user(self, payload: LoginRequest) -> User:
    #     async with readonly_session() as session:
    #         stmt = select(User).where(User.username == payload.username)
    #         user = (await session.execute(stmt)).scalar_one_or_none()
    #         if user is None or not verify_password(payload.password, user.password_hash):
    #             raise UnauthorizedError("认证失败")
    #         return user

    # async def change_password(self, payload: ChangePasswordRequest) -> None:
    #     async with write_session() as session:
    #         stmt = select(User).where(User.username == payload.username)
    #         user = (await session.execute(stmt)).scalar_one_or_none()
    #         if user is None:
    #             raise NotFoundError("用户不存在")
    #         if not verify_password(payload.old_password, user.password_hash):
    #             raise UnauthorizedError("旧密码不正确")
    #         user.password_hash = hash_password(payload.new_password)
    #         await session.flush()
