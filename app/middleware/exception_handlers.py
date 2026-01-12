import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError

from app.common.constants import (
    DUPLICATE_RESOURCE_ERROR,
    UNKNOWN_ERROR,
    VALIDATION_ERROR,
)
from app.common.errors import DuplicateResourceError, ValidationError
from app.schemas import ErrorResponse

logger = logging.getLogger("uvicorn")


# 从 HTTPException 中扁平化提取错误消息
def _extract_message_from_detail(detail: object) -> str:
    if isinstance(detail, str):
        return detail
    if isinstance(detail, dict):
        message = detail.get("message")
        if isinstance(message, str) and message:
            return message
        inner_detail = detail.get("detail")
        if isinstance(inner_detail, str) and inner_detail:
            return inner_detail
        return str(detail)
    if isinstance(detail, list) and detail:
        first = detail[0]
        if isinstance(first, dict):
            msg = first.get("msg") or first.get("message") or first.get("detail")
            if isinstance(msg, str) and msg:
                return msg
        return str(first)
    return UNKNOWN_ERROR


# 从 RequestValidationError 中扁平化提取错误消息
def _extract_message_from_validation_errors(errors: list[dict]) -> str:
    if not errors:
        return VALIDATION_ERROR
    first = errors[0]
    msg = first.get("msg")
    if not isinstance(msg, str) or not msg:
        return VALIDATION_ERROR
    loc = first.get("loc")
    if isinstance(loc, list | tuple) and loc:
        loc_str = ".".join(str(x) for x in loc)
        return f"{loc_str}: {msg}"
    return msg


# 注册异常处理程序
def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(
        DuplicateResourceError,
        duplicate_resource_exception_handler,  # type: ignore
    )
    app.add_exception_handler(
        ValidationError,
        validation_exception_handler,  # type: ignore
    )
    app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore
    app.add_exception_handler(
        RequestValidationError,
        request_validation_exception_handler,  # type: ignore
    )
    app.add_exception_handler(
        PydanticValidationError,
        pydantic_validation_exception_handler,  # type: ignore
    )
    app.add_exception_handler(Exception, unknown_exception_handler)


# 未知异常处理程序
async def unknown_exception_handler(request: Request, exc: Exception):
    logger.exception(UNKNOWN_ERROR, exc_info=exc)
    return ErrorResponse.build(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message=UNKNOWN_ERROR,
    )


# 资源重复异常处理程序
async def duplicate_resource_exception_handler(
    request: Request, exc: DuplicateResourceError
):
    logger.exception(DUPLICATE_RESOURCE_ERROR, exc_info=exc)
    return ErrorResponse.build(
        status_code=status.HTTP_409_CONFLICT,
        message=str(exc),
    )


# 校验异常处理程序
async def validation_exception_handler(request: Request, exc: ValidationError):
    logger.exception(VALIDATION_ERROR, exc_info=exc)
    return ErrorResponse.build(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message=str(exc),
    )


# HTTP 异常处理程序
async def http_exception_handler(request: Request, exc: HTTPException):
    message = _extract_message_from_detail(exc.detail)
    return ErrorResponse.build(status_code=exc.status_code, message=message)


# 请求校验异常处理程序
async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    message = _extract_message_from_validation_errors(exc.errors())
    logger.exception(VALIDATION_ERROR, exc_info=exc)
    return ErrorResponse.build(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message=message,
    )


# Pydantic 校验异常处理程序
async def pydantic_validation_exception_handler(
    request: Request, exc: PydanticValidationError
):
    message = _extract_message_from_validation_errors(exc.errors())
    logger.exception(VALIDATION_ERROR, exc_info=exc)
    return ErrorResponse.build(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message=message,
    )
