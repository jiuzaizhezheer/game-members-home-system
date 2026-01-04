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

# JWT
SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)
)  # 30 minutes
REFRESH_TOKEN_EXPIRE_DAYS: int = int(
    os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7)
)  # 7 days
