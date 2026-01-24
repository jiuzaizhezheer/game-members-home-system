from typing import Generic, TypeVar

from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    message: str = Field(description="成功响应信息")
    data: T | None = Field(default=None, description="成功响应数据")


class ErrorResponse:
    @staticmethod
    def build(
        status_code: int, message: str, headers: dict[str, str] | None = None
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status_code, content={"message": message}, headers=headers
        )
