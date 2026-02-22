"""消息路由：消息资源接口"""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query, status

from app.api.deps import get_current_user_id, get_message_service
from app.api.role import require_member_or_merchant
from app.common.constants import GET_SUCCESS
from app.schemas import SuccessResponse
from app.schemas.message import (
    ConversationListOut,
    MessageListOut,
    MessageSendIn,
)
from app.services import MessageService

message_router = APIRouter()


@message_router.get(
    path="/unread/count",
    dependencies=[require_member_or_merchant],
    response_model=SuccessResponse[int],
    status_code=status.HTTP_200_OK,
)
async def get_unread_count(
    user_id: Annotated[str, Depends(get_current_user_id)],
    message_service: Annotated[MessageService, Depends(get_message_service)],
) -> SuccessResponse[int]:
    """获取未读消息总数"""
    count = await message_service.get_unread_count(user_id)
    return SuccessResponse[int](message=GET_SUCCESS, data=count)


@message_router.get(
    path="/",
    dependencies=[require_member_or_merchant],
    response_model=SuccessResponse[ConversationListOut],
    status_code=status.HTTP_200_OK,
)
async def get_conversations(
    user_id: Annotated[str, Depends(get_current_user_id)],
    message_service: Annotated[MessageService, Depends(get_message_service)],
) -> SuccessResponse[ConversationListOut]:
    """获取会话列表"""
    result = await message_service.get_conversations(user_id)
    return SuccessResponse[ConversationListOut](message=GET_SUCCESS, data=result)


@message_router.post(
    path="/",
    dependencies=[require_member_or_merchant],
    response_model=SuccessResponse[None],
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    user_id: Annotated[str, Depends(get_current_user_id)],
    payload: Annotated[MessageSendIn, Body(description="发送消息请求")],
    message_service: Annotated[MessageService, Depends(get_message_service)],
) -> SuccessResponse[None]:
    """发送消息"""
    await message_service.send_message(user_id, payload)
    return SuccessResponse[None](message="发送成功")


@message_router.get(
    path="/{partner_user_id}",
    dependencies=[require_member_or_merchant],
    response_model=SuccessResponse[MessageListOut],
    status_code=status.HTTP_200_OK,
)
async def get_messages(
    user_id: Annotated[str, Depends(get_current_user_id)],
    partner_user_id: Annotated[str, Path(description="对方用户 ID")],
    message_service: Annotated[MessageService, Depends(get_message_service)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 30,
) -> SuccessResponse[MessageListOut]:
    """获取与某人的消息历史"""
    result = await message_service.get_messages(
        user_id, partner_user_id, page, page_size
    )
    return SuccessResponse[MessageListOut](message=GET_SUCCESS, data=result)


@message_router.patch(
    path="/{partner_user_id}/read",
    dependencies=[require_member_or_merchant],
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
)
async def mark_as_read(
    user_id: Annotated[str, Depends(get_current_user_id)],
    partner_user_id: Annotated[str, Path(description="对方用户 ID")],
    message_service: Annotated[MessageService, Depends(get_message_service)],
) -> SuccessResponse[None]:
    """标记会话已读"""
    await message_service.mark_as_read(user_id, partner_user_id)
    return SuccessResponse[None](message="标记成功")
