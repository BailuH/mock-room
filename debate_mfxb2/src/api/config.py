"""API configuration settings for Digital Court backend."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration settings for the FastAPI application."""

    # ==================== API Server ====================
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # ==================== CORS ====================
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:8080",
        "http://localhost:8083",  # court_vue3
    ]

    # ==================== Graph/Checkpoint ====================
    checkpoint_namespace: str = "court_trial"

    # ==================== 数据库配置 (Docker PostgreSQL) ====================
    # Docker 配置说明：
    # 1. 启动 Docker 服务：docker-compose up -d
    # 2. 确保 PostgreSQL (localhost:5432) 已启动
    # ========================================================================
    database_url: str = "postgresql+asyncpg://postgres:court123@localhost:5432/court_system"

    # ==================== MinIO 对象存储配置 (Docker MinIO) ====================
    # Console: http://localhost:9001 (用户名: minioadmin, 密码: minio123)
    # 需要先在 MinIO 中创建名为 "court-cases" 的桶
    # ===========================================================================
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minio123"
    minio_bucket: str = "court-cases"
    minio_secure: bool = False  # 如果没有配置 SSL (HTTPS)，设为 False

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
