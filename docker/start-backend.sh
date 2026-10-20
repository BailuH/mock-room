#!/bin/bash
# !! DEPRECATED !! 仅供 all-in-one Dockerfile 回滚使用。
# 新部署：backend 镜像直接 CMD ["uvicorn", ...]，depends_on postgres.healthcondition 替代 poll。
# 等待 PostgreSQL 就绪后再启动后端，确保自动建表成功
set -e

echo "[backend] waiting for PostgreSQL..."
until pg_isready -h 127.0.0.1 -p 5432 -U postgres >/dev/null 2>&1; do
    sleep 1
done
echo "[backend] PostgreSQL is ready, starting uvicorn..."

cd /app/backend
exec uvicorn src.api.main:app --host 0.0.0.0 --port 8000
