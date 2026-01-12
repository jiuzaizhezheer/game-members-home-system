import json

import pytest
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request

from app.middleware.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)


@pytest.mark.asyncio
async def test_http_exception_returns_message_and_data():
    request = Request({"type": "http", "method": "GET", "path": "/"})
    exc = HTTPException(status_code=401, detail="Token expired")
    res = await http_exception_handler(request, exc)

    assert res.status_code == 401
    assert json.loads(res.body) == {"message": "Token expired"}


@pytest.mark.asyncio
async def test_http_exception_detail_dict_message_is_used():
    request = Request({"type": "http", "method": "GET", "path": "/"})
    exc = HTTPException(status_code=400, detail={"message": "bad request"})
    res = await http_exception_handler(request, exc)

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
