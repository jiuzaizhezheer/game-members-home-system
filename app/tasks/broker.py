from taskiq import TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource
from taskiq_aio_pika import AioPikaBroker

from app.core import config

# 选择 RabbitMQ 作为消息中间件
broker = AioPikaBroker(config.RABBITMQ_URL)

# 定义调度器，用于处理通过装饰器 schedule 参数定义的定时任务
scheduler = TaskiqScheduler(
    broker=broker,
    sources=[LabelScheduleSource(broker)],
)
