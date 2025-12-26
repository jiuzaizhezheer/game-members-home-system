import logging

from fastapi import FastAPI, Request, status

from app.common.constants import (
    DUPLICATE_RESOURCE_ERROR,
    UNKNOWN_ERROR,
    VALIDATION_ERROR,
)
from app.common.errors import DuplicateResourceError, ValidationError
from app.model import ErrorResponse

logger = logging.getLogger("uvicorn")


# 注册异常处理程序
def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(
        DuplicateResourceError, duplicate_resource_exception_handler
    )
    app.add_exception_handler(ValidationError, validation_exception_handler)
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
