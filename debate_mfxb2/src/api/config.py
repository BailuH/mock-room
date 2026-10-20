"""API configuration settings for Digital Court backend.

默认值面向本地开发（uvicorn 直接跑在宿主机，配合 `docker compose up postgres minio`）。
容器化部署时由 `docker-compose.yml` 的 environment 字段强制覆盖为容器网络拓扑
（postgres:5432 / minio:9000），.env 与本文件中的默认值不会生效。
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration settings for the FastAPI application."""

    # ==================== API Server ====================
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # ==================== CORS ====================
    # 本地开发：court_vue3 (8083) 与 mock-court vite dev (5173) 都需要
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:8080",
        "http://localhost:8083",  # court_vue3
        "http://localhost",       # frontend nginx 容器同源
    ]

    # ==================== Graph/Checkpoint ====================
    checkpoint_namespace: str = "court_trial"

    # ==================== 数据库 ====================
    # 本地开发：docker compose up postgres -> localhost:5432
    # 容器内：compose 会覆盖为 postgres:5432
    database_url: str = "postgresql+asyncpg://postgres:court123@localhost:5432/court_system"

    # ==================== MinIO 对象存储 ====================
    # 本地开发：docker compose up minio -> localhost:9000
    # 容器内：compose 会覆盖为 minio:9000
    # 注意：presigned URL 中的 hostname 取自此 endpoint；
    #       浏览器需能解析该 hostname，本地开发用 localhost 即可。
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minio123"
    minio_bucket: str = "court-cases"
    minio_secure: bool = False  # 没有配置 SSL (HTTPS) 时设为 False

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
