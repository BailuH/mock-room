#!/bin/bash
# 一体化容器入口：初始化 PostgreSQL（仅首次），然后由 supervisord 统一管理所有服务
set -e

PG_BIN=/usr/lib/postgresql/16/bin

mkdir -p "$PGDATA" /var/run/postgresql /minio/data /var/log/supervisor
chown -R postgres:postgres "$PGDATA" /var/run/postgresql

if [ ! -s "$PGDATA/PG_VERSION" ]; then
    echo "[entrypoint] 首次启动，初始化 PostgreSQL 数据库..."
    su -s /bin/bash postgres -c "$PG_BIN/initdb -D '$PGDATA' -U postgres --auth-local=trust --auth-host=scram-sha-256"
    su -s /bin/bash postgres -c "$PG_BIN/pg_ctl -D '$PGDATA' -w -t 120 start"
    su -s /bin/bash postgres -c "psql -c \"ALTER USER postgres PASSWORD 'court123';\""
    su -s /bin/bash postgres -c "psql -c 'CREATE DATABASE court_system;'"
    su -s /bin/bash postgres -c "$PG_BIN/pg_ctl -D '$PGDATA' -w stop"
    echo "[entrypoint] PostgreSQL 初始化完成"
fi

exec supervisord -c /etc/supervisor/conf.d/supervisord.conf
