# ============================================================
# 后端镜像：FastAPI only
#   - 不再内嵌 PostgreSQL / MinIO / nginx / supervisord
#   - 数据库与对象存储由 docker-compose 中的独立服务提供
#   - .env 不打入镜像，运行时由 compose env_file / -e 注入
# ============================================================
# 基础镜像可通过构建参数覆盖，便于网络受限环境使用镜像源：
#   docker build -f docker/backend.Dockerfile \
#     --build-arg PYTHON_IMAGE=docker.m.daocloud.io/library/python:3.13-slim-bookworm \
#     -t digital-court:backend ./debate_mfxb2
# ============================================================
ARG PYTHON_IMAGE=python:3.13-slim-bookworm
FROM ${PYTHON_IMAGE}

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# ---------- 系统依赖 ----------
# curl 用于健康检查；build-essential/gcc 仅在(asyncpg/sqlalchemy)需要编译时安装
# asyncpg 提供 wheel，通常无需编译；如镜像源无 wheel 再补 build-essential
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ---------- 安装 uv 并装依赖（利用 Docker 缓存层） ----------
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv \
    && uv pip install --system --no-cache -r pyproject.toml

# ---------- 后端源码 ----------
# 注意：不 COPY .env，运行时由 docker-compose env_file 注入
COPY src ./src
COPY langgraph.json ./langgraph.json

EXPOSE 8000

# 健康检查：/health 端点
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=5 \
    CMD curl -fsS http://127.0.0.1:8000/health || exit 1

# uvicorn 直接启动；开发期挂载 src 即可热重载，无需额外配置
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
