from taskiq_aio_pika import AioPikaBroker

from app.core import config

# 选择 RabbitMQ 作为消息中间件，显式不配置 Result Backend（不使用 Redis 存储结果）
broker = AioPikaBroker(config.RABBITMQ_URL)

# 如果未来需要集成 FastAPI 的依赖注入，可以使用 taskiq-fastapi
# from taskiq_fastapi import FastAPIInjector
# FastAPIInjector(broker, "app.main:app")
