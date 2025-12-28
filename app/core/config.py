import os

from dotenv import load_dotenv

# 加载 .env 文件到环境变量
load_dotenv()


PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Game Members Home System")
VERSION: str = os.getenv("VERSION", "1.0.0")
DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

# Database
POSTGRES_USER: str = os.getenv("POSTGRES_USER", "root")
POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "123456")
POSTGRES_DB: str = os.getenv("POSTGRES_DB", "game_member_hub")

# 如果环境变量未设置，提供一个默认值或抛出错误
DATABASE_URL: str = (
    f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@127.0.0.1:5432/{POSTGRES_DB}"
)

# Redis
REDIS_HOST: str = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB: int = int(os.getenv("REDIS_DB", 8))

REDIS_URL: str = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
