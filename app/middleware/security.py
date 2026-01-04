import logging
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import ExpiredSignatureError, JWTError

from app.utils.token_util import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/users/login",
    refreshUrl="commons/token/refresh",
)

logger = logging.getLogger("uvicorn")


class RoleChecker:
    def __init__(self, *allowed_roles: str):
        self.allowed_roles = allowed_roles

    async def __call__(
        self, request: Request, token: Annotated[str, Depends(oauth2_scheme)]
    ):
        logger.info(f"access token: {token}")
        try:
            payload = decode_access_token(token)
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={
                    "WWW-Authenticate": 'Bearer error="invalid_token", error_description="The token is expired"'
                },
            ) from None
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            ) from None

        role = payload.get("role")
        user_id = payload.get("sub")
        logger.info(f"role: {role}")
        logger.info(f"user_id: {user_id}")

        if self.allowed_roles and role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted",
            )

        # 将 user_id 存储到 request.state 中，以便后续使用
        request.state.user_id = user_id
