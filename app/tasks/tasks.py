import logging

from app.tasks.broker import broker

logger = logging.getLogger(__name__)


@broker.task(task_name="check_order_timeout", schedule=[{"cron": "* * * * *"}])
async def check_order_timeout():
    """
    定期检查并自动确认收货
    """
    from app.api.deps import get_order_service

    service = get_order_service()
    try:
        count = await service.auto_receipt_orders(days=7)
        if count > 0:
            logger.info(f"[AutoReceipt] Successfully confirmed {count} orders.")
        else:
            logger.info("[AutoReceipt] No expired orders found.")
        return count
    except Exception as e:
        logger.error(f"[AutoReceipt] Error occurred: {e}")
        return 0


@broker.task(task_name="cancel_expired_orders_task", schedule=[{"cron": "* * * * *"}])
async def cancel_expired_orders_task():
    """
    定期扫描并自动取消超过 15 分钟仍未支付的订单
    """
    from app.api.deps import get_order_service

    service = get_order_service()
    try:
        count = await service.auto_cancel_expired_orders(minutes=15)
        if count > 0:
            logger.info(
                f"[AutoCancel] Successfully cancelled {count} expired pending orders."
            )
        else:
            logger.info("[AutoCancel] No expired pending orders found.")
        return count
    except Exception as e:
        logger.error(f"[AutoCancel] Error occurred: {e}")
        return 0


@broker.task(
    task_name="cancel_unpaid_order_task",
    max_retries=3,
)
async def cancel_unpaid_order_task(order_id: str, user_id: str):
    """
    超时自动取消未支付订单
    """
    from app.api.deps import get_order_service

    service = get_order_service()
    try:
        await service.cancel_order(user_id=user_id, order_id=order_id)
        logger.info(f"[AutoCancel] Successfully cancelled order {order_id}.")
    except Exception as e:
        logger.error(f"[AutoCancel] Skipped or failed for order {order_id}: {e}")
        raise e


@broker.task(
    task_name="send_verification_email_task",
    max_retries=3,  # 在 SMTP 失败或网络抖动时自动重试 3 次
)
async def send_verification_email_task(email: str, code: str):
    """
    发送注册验证码邮件
    """
    from app.api.deps import get_email_service

    service = get_email_service()

    success = await service.send_verification_email(email, code)
    if not success:
        raise Exception("Failed to send email")
