import asyncio

from celery import Celery  # type: ignore
from celery.schedules import crontab  # type: ignore

from app.core import config
from app.services.order_service import OrderService

# 实例化 Celery
# 注意：在 Windows 上运行 Worker 需要使用 pool=solo，例如：
# celery -A app.tasks.celery_worker worker --loglevel=info -P solo
celery_app = Celery(
    "worker",
    broker=config.RABBITMQ_URL,
    backend=config.REDIS_URL,
)

# 配置时区
celery_app.conf.timezone = "UTC"

# 配置定时任务调度
celery_app.conf.beat_schedule = {
    "check-order-timeout-every-minute": {  # 为了演示方便，这里设为每分钟
        "task": "app.tasks.celery_worker.check_order_timeout",
        "schedule": crontab(minute="*"),
        # 生产环境建议使用：
        # 'schedule': crontab(minute=0, hour='*'), # 每小时执行一次
    },
}


@celery_app.task
def check_order_timeout():
    """
    Celery Task: 定期检查并自动确认收货
    """
    print("Running task: check_order_timeout")

    async def _run():
        service = OrderService()
        try:
            # 自动确认超过 7 天未收货的订单
            count = await service.auto_receipt_orders(days=7)
            if count > 0:
                print(f"[AutoReceipt] Successfully confirmed {count} orders.")
            else:
                print("[AutoReceipt] No expired orders found.")
            return count
        except Exception as e:
            print(f"[AutoReceipt] Error occurred: {e}")
            return 0

    # 在同步的 Celery Task 中运行异步代码
    try:
        # 获取或创建新的事件循环
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(_run())
    except Exception as e:
        # 如果 loop 已经关闭或不可用，尝试用 asyncio.run
        print(f"Fallback to asyncio.run due to: {e}")
        return asyncio.run(_run())
