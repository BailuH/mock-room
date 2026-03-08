"""SQLAlchemy 基础配置和数据库连接。

Docker 配置说明：
    1. 启动 Docker 服务：docker-compose up -d
    2. 确保 PostgreSQL 容器正在运行：docker-compose ps
    3. 数据库会自动创建所需的表结构
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

from src.api.config import settings

# 创建异步引擎
# 注意：密码中的 @ 符号已在 URL 中正确编码为 %40
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,  # 开发环境下打印 SQL 语句
    pool_pre_ping=True,    # 连接前检查数据库可用性
)

# 创建异步会话工厂
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # 提交后不过期对象，允许访问
)

# 声明式基类
Base = declarative_base()


# 依赖注入：获取数据库会话
async def get_db() -> AsyncSession:
    """FastAPI 依赖注入：获取数据库会话。

    使用方式：
        @app.get("/api/cases")
        async def get_cases(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(CaseModel))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
