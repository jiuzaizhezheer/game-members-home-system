import os

from dotenv import load_dotenv

# 加载 .env 文件到环境变量
load_dotenv()


class Settings:
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Game Members Home System")
    VERSION: str = os.getenv("VERSION", "1.0.0")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    # Database
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "password")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "db")

    # 如果环境变量未设置，提供一个默认值或抛出错误
    DATABASE_URL: str = (
        f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@localhost:5432/{POSTGRES_DB}"
    )


settings = Settings()
