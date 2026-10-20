# ============================================================
# !! DEPRECATED !!  All-in-one 镜像（保留一个版本周期作回滚备份）
# ------------------------------------------------------------
# 新部署请使用 docker-compose.yml + docker/backend.Dockerfile +
# docker/frontend.Dockerfile（前后端解耦，见 START.md）。
#
# 此文件合并了 nginx + PostgreSQL + MinIO + supervisord + FastAPI，
# 前后端无法独立构建/发布/伸缩，且 .env 与密钥会被打入镜像。
# 仅当新版 compose 出现阻断性问题时临时使用：
#   docker build -t digital-court:all-in-one .
# 计划在 Phase 1（React 删除）完成后彻底移除。
# ============================================================
# 基础镜像可通过构建参数覆盖，便于在网络受限环境使用镜像源：
#   docker build \
#     --build-arg NODE_IMAGE=docker.m.daocloud.io/library/node:20-bookworm-slim \
#     --build-arg PYTHON_IMAGE=docker.m.daocloud.io/library/python:3.13-slim-bookworm \
#     -t digital-court:all-in-one .
# ============================================================
ARG NODE_IMAGE=node:20-bookworm-slim
ARG PYTHON_IMAGE=python:3.13-slim-bookworm

# ============================================================
# Stage 1: 构建 court_vue3 主前端 (Vue3 + vue-cli)
# ============================================================
FROM ${NODE_IMAGE} AS frontend-build
WORKDIR /build
# 国内构建加速；在境外服务器构建同样可用
RUN npm config set registry https://registry.npmmirror.com
COPY court_vue3/package.json court_vue3/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY court_vue3/ ./
# 同域反代：baseURL 设为空串，API 请求走 nginx 反代，不再写死 localhost:8000
ARG VUE_APP_API_BASE_URL=""
ENV VUE_APP_API_BASE_URL=${VUE_APP_API_BASE_URL}
ENV NODE_OPTIONS=--max-old-space-size=4096
RUN npm run build

# ============================================================
# Stage 2: 构建 mock-court 庭审模拟页 (React + Vite)
# ============================================================
FROM ${NODE_IMAGE} AS mock-court-build
WORKDIR /build
RUN npm config set registry https://registry.npmmirror.com
COPY mock-court/package.json mock-court/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY mock-court/ ./
# vite.config.ts 中生产构建自动使用 base=/mock-court/
RUN npm run build

# ============================================================
# Stage 3: 一体化运行时
#   nginx (80) : court_vue3 / mock-court 静态资源 + /api /ws 反代
#   FastAPI    : 127.0.0.1:8000 (supervisord 管理)
#   PostgreSQL : 127.0.0.1:5432 (数据卷 /var/lib/postgresql/data)
#   MinIO      : :9000 (API, 数据卷 /minio/data), :9001 (Console)
# ============================================================
FROM ${PYTHON_IMAGE} AS runtime

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PGDATA=/var/lib/postgresql/data

# ---------- 系统依赖: PostgreSQL 16 (PGDG) + nginx + supervisor ----------
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl ca-certificates gnupg \
        nginx supervisor \
    && install -d /usr/share/postgresql-common/pgdg \
    && curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc \
        | gpg --dearmor -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.gpg \
    && echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.gpg] http://apt.postgresql.org/pub/repos/apt bookworm-pgdg main" \
        > /etc/apt/sources.list.d/pgdg.list \
    && apt-get update && apt-get install -y --no-install-recommends postgresql-16 \
    && rm -rf /var/lib/apt/lists/*

# ---------- MinIO (固定版本) ----------
ARG MINIO_VERSION=RELEASE.2025-09-07T16-13-09Z
RUN curl -fsSL -o /usr/local/bin/minio \
        "https://dl.min.io/server/minio/release/linux-amd64/archive/minio.${MINIO_VERSION}" \
    && chmod +x /usr/local/bin/minio

# ---------- 后端 Python 依赖 (uv, 使用 pyproject 中配置的清华镜像) ----------
WORKDIR /app/backend
COPY debate_mfxb2/pyproject.toml debate_mfxb2/uv.lock ./
RUN pip install --no-cache-dir uv \
    && uv pip install --system --no-cache -r pyproject.toml

# ---------- 后端代码与默认配置 (.env 中的密钥可用 -e 运行时覆盖) ----------
COPY debate_mfxb2/src ./src
COPY debate_mfxb2/.env ./.env

# ---------- 前端产物 ----------
COPY --from=frontend-build /build/dist /app/frontend
COPY --from=mock-court-build /build/dist /app/mock-court

# ---------- nginx / supervisor / 启动脚本 ----------
COPY docker/nginx.conf /etc/nginx/conf.d/app.conf
RUN rm -f /etc/nginx/sites-enabled/default
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY docker/start-backend.sh /usr/local/bin/start-backend.sh
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/start-backend.sh /usr/local/bin/entrypoint.sh

ENV MINIO_ROOT_USER=minioadmin \
    MINIO_ROOT_PASSWORD=minio123

VOLUME ["/var/lib/postgresql/data", "/minio/data"]

# 80: 应用入口 (主前端 + 庭审模拟页 + API/WebSocket 反代)
# 9000: MinIO API (浏览器直连上传/预览文件, 预签名 URL)
# 9001: MinIO 管理控制台
EXPOSE 80 9000 9001

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
