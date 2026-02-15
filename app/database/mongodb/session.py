from typing import Any

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import MONGO_DATABASE_URL, MONGO_DB
from app.database.mongodb.base_entity import BaseEntity
from app.entity import mongodb as mongodb_models

# 创建全局 MongoDB 客户端实例 (等同于 PG 的 pg_engine)
mongodb_client: AsyncIOMotorClient = AsyncIOMotorClient(
    MONGO_DATABASE_URL,
    maxPoolSize=10,
    minPoolSize=5,
)


async def init_mongodb():
    """
    初始化 MongoDB 连接并自动绑定所有 Beanie 模型
    """
    # 获取数据库实例
    database: Any = mongodb_client[MONGO_DB]

    # 动态获取 app.entity.mongodb 中定义的所有继承自 BaseEntity 的模型类
    document_models = [
        model
        for model in mongodb_models.__dict__.values()
        if isinstance(model, type) and issubclass(model, BaseEntity)
    ]

    # 初始化 Beanie (将全局 client 绑定的 database 注入模型)
    await init_beanie(
        database=database,
        document_models=document_models,
    )
