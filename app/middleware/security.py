import logging
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import ExpiredSignatureError, JWTError

from app.common.constants import (
    ACCESS_TOKEN_EXPIRED,
    ACCESS_TOKEN_INVALID,
    PERMISSION_DENIED,
    WWW_AUTH_EXPIRED,
    WWW_AUTH_INVALID,
)
from app.common.errors import PermissionDeniedError, UnauthorizedError
from app.utils import decode_access_token

logger = logging.getLogger("uvicorn")


class RoleChecker:
    def __init__(self, *allowed_roles: str):
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        request: Request,
        token_credentials: Annotated[
            HTTPAuthorizationCredentials, Depends(HTTPBearer())
        ],
    ):
        token = token_credentials.credentials
        logger.info(f"access token: {token}")
        try:
            payload = decode_access_token(token)
        except ExpiredSignatureError:
            raise UnauthorizedError(
                detail=ACCESS_TOKEN_EXPIRED,
                headers={"WWW-Authenticate": WWW_AUTH_EXPIRED},
            ) from None
        except JWTError:
            raise UnauthorizedError(
                detail=ACCESS_TOKEN_INVALID,
                headers={"WWW-Authenticate": WWW_AUTH_INVALID},
            ) from None

        role = payload.get("role")
        user_id = payload.get("sub")
        logger.info(f"role: {role}")
        logger.info(f"user_id: {user_id}")

        if self.allowed_roles and role not in self.allowed_roles:
            raise PermissionDeniedError(
                detail=PERMISSION_DENIED,
            )

        # 将 user_id 存储到 request.state 中，以便后续使用
        request.state.user_id = user_id
