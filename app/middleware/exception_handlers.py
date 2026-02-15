import logging
from collections.abc import Mapping, Sequence

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError

from app.common.constants import (
    UNKNOWN_ERROR,
    VALIDATION_ERROR,
)
from app.common.errors import BusinessError
from app.schemas import ErrorResponse

logger = logging.getLogger("uvicorn")


# 从 RequestValidationError 中扁平化提取错误消息
def _extract_message_from_validation_errors(errors: Sequence[object]) -> str:
    if not errors:
        return VALIDATION_ERROR
    first = errors[0]
    if not isinstance(first, Mapping):
        return VALIDATION_ERROR
    msg = first.get("msg")
    if not isinstance(msg, str) or not msg:
        return VALIDATION_ERROR
    loc = first.get("loc")
    if isinstance(loc, Sequence) and loc:
        loc_str = ".".join(str(x) for x in loc)
        return f"{loc_str}: {msg}"
    return msg


# 注册异常处理程序
def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(
        RequestValidationError,
        request_validation_exception_handler,  # type: ignore
    )
    app.add_exception_handler(
        BusinessError,
        business_exception_handler,  # type: ignore
    )
    app.add_exception_handler(Exception, unknown_exception_handler)


# 服务器未知异常处理程序
async def unknown_exception_handler(request: Request, exc: Exception):
    logger.exception(UNKNOWN_ERROR, exc_info=exc)
    return ErrorResponse.build(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message=UNKNOWN_ERROR,
    )


# 基础业务异常处理程序
async def business_exception_handler(request: Request, exc: BusinessError):
    logger.exception(exc.detail, exc_info=exc)
    return ErrorResponse.build(
        status_code=exc.status_code,
        message=exc.detail,
        headers=dict(exc.headers) if exc.headers else None,
    )


# 请求校验异常处理程序
async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    message = _extract_message_from_validation_errors(exc.errors())
    logger.exception(message, exc_info=exc)
    return ErrorResponse.build(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message=message,
    )
