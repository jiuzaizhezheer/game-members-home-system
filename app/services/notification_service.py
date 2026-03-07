import logging
import uuid

from app.core.websocket_manager import ws_manager
from app.database.pgsql import get_pg
from app.entity.pgsql.notifications import SystemNotification
from app.repo import notifications_repo
from app.schemas.notification import SystemNotificationOut

logger = logging.getLogger(__name__)


class NotificationService:
    """系统消息通知服务"""

    async def get_my_notifications(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        notification_type: str | None = None,
    ) -> tuple[list[SystemNotificationOut], int]:
        """获取我的消息列表"""
        async with get_pg() as session:
            items, total = await notifications_repo.get_list_by_user(
                session, uuid.UUID(user_id), page, page_size, notification_type
            )
            return [SystemNotificationOut.model_validate(item) for item in items], total

    async def get_unread_count(self, user_id: str) -> int:
        """获取未读消息数"""
        async with get_pg() as session:
            count = await notifications_repo.get_unread_count(
                session, uuid.UUID(user_id)
            )
            return count

    async def mark_as_read(self, user_id: str, notification_id: str) -> bool:
        """将某条消息标记为已读"""
        async with get_pg() as session:
            # 校验归属
            notification = await notifications_repo.get_by_id(
                session, uuid.UUID(notification_id)
            )
            if not notification or str(notification.user_id) != user_id:
                return False

            success = await notifications_repo.mark_as_read(
                session, uuid.UUID(notification_id)
            )
            if success:
                await session.commit()
            return success

    async def mark_all_as_read(self, user_id: str) -> int:
        """全部标记已读"""
        async with get_pg() as session:
            count = await notifications_repo.mark_all_as_read(
                session, uuid.UUID(user_id)
            )
            if count > 0:
                await session.commit()
            return count

    # ===== 内部业务分发通知的方法 =====

    async def create_notification(
        self,
        user_id: str,
        type_: str,
        title: str,
        content: str,
        link: str | None = None,
    ) -> None:
        """
        内部创建通知，包含异常捕获，确保不影响主业务
        """
        try:
            async with get_pg() as session:
                notification = SystemNotification(
                    user_id=uuid.UUID(user_id),
                    type=type_,
                    title=title,
                    content=content,
                    link=link,
                )
                await notifications_repo.create(session, notification)
                await session.commit()

                # 推送 WebSocket 消息
                payload = {
                    "type": "NEW_NOTIFICATION",
                    "data": SystemNotificationOut.model_validate(
                        notification
                    ).model_dump(mode="json"),
                }
                await ws_manager.broadcast_to_user(user_id, payload)
        except Exception as e:
            # 只记录日志，不阻断发货、退款、点赞等主流程
            logger.error(f"Failed to create notification for user {user_id}: {e}")


notification_service = NotificationService()
