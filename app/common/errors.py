from fastapi import HTTPException, status


# 基础业务异常
class BusinessError(HTTPException):
    def __init__(
        self,
        detail: str = "业务请求异常",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        headers: dict[str, str] | None = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


# 重复资源
class DuplicateResourceError(BusinessError):
    def __init__(self, detail: str = "资源已存在"):
        super().__init__(detail=detail, status_code=status.HTTP_409_CONFLICT)


# 校验异常
class ValidationError(BusinessError):
    def __init__(self, detail: str = "数据校验失败"):
        super().__init__(
            detail=detail, status_code=status.HTTP_422_UNPROCESSABLE_CONTENT
        )


# 资源不存在
class NotFoundError(BusinessError):
    def __init__(self, detail: str = "请求的资源未找到"):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


# 权限不足
class PermissionDeniedError(BusinessError):
    def __init__(self, detail: str = "权限不足"):
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)


# 请求过于频繁
class TooManyRequestsError(BusinessError):
    def __init__(self, detail: str = "请求过于频繁"):
        super().__init__(detail=detail, status_code=status.HTTP_429_TOO_MANY_REQUESTS)


# 未授权
class UnauthorizedError(BusinessError):
    def __init__(self, detail: str = "未授权", headers: dict[str, str] | None = None):
        super().__init__(
            detail=detail, status_code=status.HTTP_401_UNAUTHORIZED, headers=headers
        )
