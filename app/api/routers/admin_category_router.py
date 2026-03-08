from typing import Annotated

from fastapi import APIRouter, Depends, Path, status

from app.api.deps import get_admin_service
from app.api.role import require_admin
from app.common.constants import (
    DELETE_SUCCESS,
    GET_SUCCESS,
    POST_SUCCESS,
    UPDATE_SUCCESS,
)
from app.schemas import SuccessResponse
from app.schemas.category import CategoryCreateIn, CategoryOut, CategoryUpdateIn
from app.services import AdminService

admin_category_router = APIRouter()


@admin_category_router.get(
    path="/",
    dependencies=[require_admin],
    response_model=SuccessResponse[list[CategoryOut]],
    status_code=status.HTTP_200_OK,
)
async def get_categories(
    admin_service: Annotated[AdminService, Depends(get_admin_service)],
) -> SuccessResponse[list[CategoryOut]]:
    data = await admin_service.get_categories()
    return SuccessResponse[list[CategoryOut]](message=GET_SUCCESS, data=data)


@admin_category_router.post(
    path="/",
    dependencies=[require_admin],
    response_model=SuccessResponse[CategoryOut],
    status_code=status.HTTP_200_OK,
)
async def create_category(
    payload: CategoryCreateIn,
    admin_service: Annotated[AdminService, Depends(get_admin_service)],
) -> SuccessResponse[CategoryOut]:
    data = await admin_service.create_category(payload)
    return SuccessResponse[CategoryOut](message=POST_SUCCESS, data=data)


@admin_category_router.patch(
    path="/{id}",
    dependencies=[require_admin],
    response_model=SuccessResponse[CategoryOut],
    status_code=status.HTTP_200_OK,
)
async def update_category(
    id: Annotated[str, Path(description="分类ID")],
    payload: CategoryUpdateIn,
    admin_service: Annotated[AdminService, Depends(get_admin_service)],
) -> SuccessResponse[CategoryOut]:
    data = await admin_service.update_category(id, payload)
    return SuccessResponse[CategoryOut](message=UPDATE_SUCCESS, data=data)


@admin_category_router.delete(
    path="/{id}",
    dependencies=[require_admin],
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
)
async def delete_category(
    id: Annotated[str, Path(description="分类ID")],
    admin_service: Annotated[AdminService, Depends(get_admin_service)],
) -> SuccessResponse[None]:
    await admin_service.delete_category(id)
    return SuccessResponse[None](message=DELETE_SUCCESS)
