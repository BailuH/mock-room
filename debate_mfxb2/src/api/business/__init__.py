"""业务模块。

此模块包含从 court_fastapi 迁移的业务逻辑：
    - storage.py: MinIO 对象存储服务
    - auth.py: 用户认证（登录/注册）
    - cases.py: 案件管理 CRUD
    - files.py: 文件上传和管理

Docker 配置说明：
    1. 启动 Docker 服务：docker-compose up -d
    2. 创建 MinIO 桶：访问 http://localhost:9001 创建 "court-cases" 桶
    3. 确保 PostgreSQL 和 MinIO 都在运行
"""

from src.api.business.storage import MinIOService, get_minio
from src.api.business.auth import router as auth_router
from src.api.business.cases import router as cases_router
from src.api.business.files import router as files_router
from src.api.business.storage import router as storage_router

__all__ = [
    "MinIOService",
    "get_minio",
    "auth_router",
    "cases_router",
    "files_router",
    "storage_router",
]
