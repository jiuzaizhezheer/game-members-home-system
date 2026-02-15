import os

from dotenv import load_dotenv

# 加载 .env 文件到环境变量
load_dotenv()


PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Game Members Home System")
VERSION: str = os.getenv("VERSION", "1.0.0")
DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
ENV: str = os.getenv("ENV", "local")

# PostgreSQL
POSTGRES_USER: str = os.getenv("POSTGRES_USER", "admin")
POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "admin123")
POSTGRES_DB: str = os.getenv("POSTGRES_DB", "game_member_home")
POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "127.0.0.1")
POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", 5432))

DATABASE_URL: str = (
    f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

# MongoDB
MONGO_ROOT_USER: str = os.getenv("MONGO_ROOT_USER", "admin")
MONGO_ROOT_PASSWORD: str = os.getenv("MONGO_ROOT_PASSWORD", "admin123")
MONGO_DB: str = os.getenv("MONGO_DB", "game_member_home")
MONGO_HOST: str = os.getenv("MONGO_HOST", "127.0.0.1")
MONGO_PORT: str = os.getenv("MONGO_PORT", "27017")

MONGO_DATABASE_URL: str = (
    f"mongodb://{MONGO_ROOT_USER}:{MONGO_ROOT_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}?authSource=admin"
)

# Redis
REDIS_HOST: str = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB: int = int(os.getenv("REDIS_DB", 8))

REDIS_URL: str = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# RabbitMQ
RABBITMQ_USER: str = os.getenv("RABBITMQ_USER", "admin")
RABBITMQ_PASSWORD: str = os.getenv("RABBITMQ_PASSWORD", "admin123")
RABBITMQ_HOST: str = os.getenv("RABBITMQ_HOST", "127.0.0.1")
RABBITMQ_PORT: int = int(os.getenv("RABBITMQ_PORT", 5672))

RABBITMQ_URL: str = (
    f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:{RABBITMQ_PORT}//"
)

# JWT
SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)
)  # 30 minutes
REFRESH_TOKEN_EXPIRE_DAYS: int = int(
    os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7)
)  # 7 days
