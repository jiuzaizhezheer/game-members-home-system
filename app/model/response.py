from typing import Generic, TypeVar

from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

T = TypeVar("T")


# 成功时响应
class SuccessResponse(BaseModel, Generic[T]):
    message: str = Field(description="消息")
    data: T | None = Field(default=None, description="响应数据")


# 异常时响应
class ErrorResponse:
    @staticmethod
    def build(status_code: int, message: str) -> JSONResponse:
        return JSONResponse(
            status_code=status_code,
            content={"message": message},
        )
