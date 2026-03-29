from typing import Annotated

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status

from app.api.deps import get_current_user_id
from app.api.role import require_member_or_merchant
from app.common.constants import GET_SUCCESS
from app.common.enums import RoleEnum
from app.core.websocket_manager import ws_manager
from app.schemas.notification import NotificationListOut, UnreadCountOut
from app.schemas.response import SuccessResponse
from app.services.notification_service import notification_service
from app.utils import decode_access_token

router = APIRouter()


@router.get(
    "/my",
    dependencies=[require_member_or_merchant],
    response_model=SuccessResponse[NotificationListOut],
    status_code=status.HTTP_200_OK,
)
async def get_my_notifications(
    user_id: Annotated[str, Depends(get_current_user_id)],
    page: Annotated[int, Query(ge=1, description="页码")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="每页数量")] = 20,
    notification_type: Annotated[str | None, Query(description="消息类型")] = None,
) -> SuccessResponse[NotificationListOut]:
    """获取我的消息列表"""
    items, total = await notification_service.get_my_notifications(
        user_id, page, page_size, notification_type
    )
    return SuccessResponse[NotificationListOut](
        message=GET_SUCCESS,
        data=NotificationListOut(
            items=items, total=total, page=page, page_size=page_size
        ),
    )


@router.get(
    "/unread-count",
    dependencies=[require_member_or_merchant],
    response_model=SuccessResponse[UnreadCountOut],
    status_code=status.HTTP_200_OK,
)
async def get_unread_count(
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> SuccessResponse[UnreadCountOut]:
    """获取我的未读消息数量"""
    count = await notification_service.get_unread_count(user_id)
    return SuccessResponse[UnreadCountOut](
        message=GET_SUCCESS, data=UnreadCountOut(count=count)
    )


@router.post(
    "/{notification_id}/read",
    dependencies=[require_member_or_merchant],
    response_model=SuccessResponse[bool],
    status_code=status.HTTP_200_OK,
)
async def mark_as_read(
    notification_id: str,
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> SuccessResponse[bool]:
    """将一条消息标为已读"""
    success = await notification_service.mark_as_read(user_id, notification_id)
    return SuccessResponse[bool](message=GET_SUCCESS, data=success)


@router.post(
    "/read-all",
    dependencies=[require_member_or_merchant],
    response_model=SuccessResponse[int],
    status_code=status.HTTP_200_OK,
)
async def mark_all_as_read(
    user_id: Annotated[str, Depends(get_current_user_id)],
) -> SuccessResponse[int]:
    """我所有的未读消息标为已读"""
    count = await notification_service.mark_all_as_read(user_id)
    return SuccessResponse[int](message=GET_SUCCESS, data=count)


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket, user_id: str, token: str | None = None
):
    """WebSocket 实时通知长连接"""
    if not token:
        await websocket.close(code=1008)
        return

    try:
        payload = decode_access_token(token)
        token_user_id = str(payload.get("sub") or "")
        role = str(payload.get("role") or "")
        if (
            not token_user_id
            or token_user_id != user_id
            or role not in {RoleEnum.MEMBER, RoleEnum.MERCHANT}
        ):
            await websocket.close(code=1008)
            return
    except Exception:
        await websocket.close(code=1008)
        return

    print(f"WS attempting connect: {user_id}")
    await ws_manager.connect(websocket, user_id)
    print(f"WS connected: {user_id}")
    try:
        while True:
            # 持续监听客户端消息（主要用于保持连接或接收心跳）
            data = await websocket.receive_text()
            # 目前不需要处理客户端发来的业务数据，仅作为心跳检测存活
            await websocket.send_text(f"pong: {data}")
    except WebSocketDisconnect:
        print(f"WS disconnected: {user_id}")
        ws_manager.disconnect(websocket, user_id)
    except Exception as e:
        print(f"WS error for {user_id}: {e}")
        ws_manager.disconnect(websocket, user_id)
