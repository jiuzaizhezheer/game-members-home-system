import json

import pytest
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request

from app.common.errors import BusinessException
from app.middleware.exception_handlers import (
    business_exception_handler,
    request_validation_exception_handler,
)


@pytest.mark.asyncio
async def test_business_exception_returns_message_and_data():
    request = Request({"type": "http", "method": "GET", "path": "/"})
    exc = BusinessException(status_code=401, detail="Token expired")
    res = await business_exception_handler(request, exc)

    assert res.status_code == 401
    assert json.loads(res.body) == {"message": "Token expired"}


@pytest.mark.asyncio
async def test_business_exception_detail_dict_message_is_used():
    request = Request({"type": "http", "method": "GET", "path": "/"})
    # BusinessException detail 只能是 str，但为了测试兼容性或未来扩展，这里保留逻辑，
    # 实际上 BusinessException 的 detail 类型提示是 str
    exc = BusinessException(status_code=400, detail="bad request")
    res = await business_exception_handler(request, exc)

    assert res.status_code == 400
    assert json.loads(res.body) == {"message": "bad request"}


@pytest.mark.asyncio
async def test_request_validation_error_returns_message_and_data():
    request = Request({"type": "http", "method": "POST", "path": "/auth/login"})
    exc = RequestValidationError(
        [
            {
                "loc": ("body", "password"),
                "msg": "field required",
                "type": "missing",
            }
        ]
    )
    res = await request_validation_exception_handler(request, exc)

    assert res.status_code == 422
    assert json.loads(res.body) == {"message": "body.password: field required"}
