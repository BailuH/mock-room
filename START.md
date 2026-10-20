# 启动指南

数字法庭系统的开发与部署说明。当前已按 `PLAN.md` Phase 2 完成 Docker 前后端解耦：
前端、后端、PostgreSQL、MinIO 各自独立容器，可独立构建/发布。

## 服务端口

| 服务 | 容器内 | 宿主机映射 | 说明 |
|------|--------|------------|------|
| frontend (nginx) | 80 | 80 | 托管 court_vue3 静态资源，反代 `/api` `/ws` 到 backend |
| backend (FastAPI) | 8000 | 8000 | WebSocket + 业务 HTTP API |
| postgres | 5432 | 5432 | 数据库 |
| minio API | 9000 | 9000 | 对象存储 API（浏览器直连上传/预览） |
| minio Console | 9001 | 9001 | MinIO 管理界面 |

> MinIO 宿主机端口已统一为 9000（旧版 9002 不一致问题已修正）。
> 如果宿主机 9000 被占用（例如 Hadoop），请修改 `docker-compose.yml` 中 minio 的 `ports` 映射，
> 并同步 `debate_mfxb2/.env` 的 `MINIO_ENDPOINT`。

---

## 一、一键启动（Docker Compose 全栈）

适合联调验证、给前端同事提供可用后端、CI 集成测试。

```bash
# 1. 准备后端环境变量
cp debate_mfxb2/.env.example debate_mfxb2/.env
#    编辑 .env，至少填入 OPENAI_API_KEY、LANGSMITH_API_KEY

# 2. 构建并启动全部服务
docker compose up -d --build
```

启动后访问：

| 服务 | 地址 |
|------|------|
| 主前端 | http://localhost |
| 后端 API | http://localhost:8000 |
| API 文档 | http://localhost:8000/docs |
| MinIO Console | http://localhost:9001 |

验证：

```bash
docker compose ps
docker compose logs -f backend
curl http://localhost/health      # 经 nginx 反代
curl http://localhost:8000/health # 直连 backend
```

停止：

```bash
docker compose down            # 保留卷
docker compose down -v         # 同时清空 postgres_data / minio_data（慎用）
```

### 独立构建/发布单端

```bash
docker compose build frontend  # 仅前端
docker compose build backend   # 仅后端
docker compose up -d frontend  # 仅重启前端，不触碰数据库/MinIO
docker compose up -d backend   # 仅重启后端
```

---

## 二、本地开发模式（推荐前后端独立开发时使用）

后端开发（你）只跑后端 + 基础设施；前端开发（同事）只跑前端 + 基础设施。

### 模式 A：后端开发

只起 postgres + minio + frontend，后端用 uvicorn 本地跑（热重载）。

```bash
# 终端 1：起基础设施 + 前端镜像
docker compose up -d postgres minio frontend

# 终端 2：本地 uvicorn（修改 debate_mfxb2/.env，使 DATABASE_URL / MINIO_ENDPOINT = localhost）
cd debate_mfxb2
uv sync                                  # 首次需安装依赖
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

确认 `debate_mfxb2/.env`：
```
DATABASE_URL=postgresql+asyncpg://postgres:court123@localhost:5432/court_system
MINIO_ENDPOINT=localhost:9000
```

### 模式 B：前端开发（交给同事）

只起 postgres + minio + backend，前端用 `npm run serve` 本地跑（HMR）。

```bash
# 终端 1：起基础设施 + 后端镜像
docker compose up -d postgres minio backend

# 终端 2：本地 vue-cli dev server
cd court_vue3
npm install
npm run serve          # 默认 http://localhost:8083
```

`court_vue3/src/config.js` 在开发态会回退到 `http://localhost:8000`，
直接访问后端容器映射的宿主机 8000 端口；如需同源可在 `vue.config.js` 加 `devServer.proxy`。

### 模式 C：纯本地（不起任何 Docker 镜像）

需要自己启动 PostgreSQL 与 MinIO（或复用 docker compose up postgres minio），
然后两端都用本地 dev server。适合调试网络/DNS 问题。

```bash
docker compose up -d postgres minio
# 后端
cd debate_mfxb2 && uvicorn src.api.main:app --reload
# 前端
cd court_vue3 && npm run serve
```

---

## 三、MinIO 桶初始化

后端启动时 `storage.py` 中的 `MinIOService._ensure_bucket_exists()` 会自动创建
`court-cases` 桶，**无需手动操作**。

如需手动操作（查看 / 上传文件）：

- Web Console：http://localhost:9001（账号见 `.env` 中 `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD`）
- 命令行：`mc alias set local http://localhost:9000 <access_key> <secret_key>`

---

## 四、账号与密钥默认值

| 服务 | 用户 | 密码 | 来源 |
|------|------|------|------|
| PostgreSQL | postgres | court123 | `docker-compose.yml` 中 `POSTGRES_PASSWORD` |
| MinIO | minioadmin | minio123 | `docker-compose.yml` 中 `MINIO_ROOT_PASSWORD` |
| 后端 LLM | - | API key | `debate_mfxb2/.env` 中 `OPENAI_API_KEY` |

> ⚠️ 生产部署务必通过 `.env` 修改默认密码，且不要把 `.env` 提交进 git。

---

## 五、目录结构与镜像职责

```
mock-room/
├── court_vue3/                  # 主前端（同事负责）
├── debate_mfxb2/                # 后端（你负责）
│   ├── .env.example             # 环境变量模板（提交进 git）
│   ├── .env                     # 实际配置（gitignored）
│   └── .dockerignore            # backend 镜像构建忽略
├── docker/
│   ├── frontend.Dockerfile      # node 构建 court_vue3 -> nginx:alpine
│   ├── backend.Dockerfile       # python:3.13-slim + uv + FastAPI
│   ├── nginx.conf               # frontend 镜像内 nginx 配置
│   ├── supervisord.conf         # !! DEPRECATED all-in-one 遗留
│   ├── entrypoint.sh            # !! DEPRECATED all-in-one 遗留
│   └── start-backend.sh         # !! DEPRECATED all-in-one 遗留
├── Dockerfile                   # !! DEPRECATED all-in-one，仅作回滚备份
├── docker-compose.yml           # 新部署编排（4 个 service）
├── .dockerignore                # frontend 镜像构建忽略（仓库根 context）
└── PLAN.md                      # 重构规划
```

镜像职责：

- **frontend**：只构建 court_vue3 + 托管 dist + 反代 `/api` `/ws`。
  更新前端不会触碰数据库或 MinIO 数据卷。
- **backend**：只装 FastAPI 依赖 + 拷 src + 跑 uvicorn。
  不再内嵌 PostgreSQL / MinIO / nginx / supervisord。
- **postgres / minio**：官方镜像，数据通过 `postgres_data` / `minio_data` 卷持久化，
  `compose down` 后数据保留，`compose down -v` 才会清空。

---

## 六、已知限制与后续工作（参见 PLAN.md）

- **mock-court 仍在仓内但不再进入 frontend 镜像**：court_vue3 中
  `HomeComponent.vue` / `MenuHome.vue` 仍有 `window.location.href = "/mock-court/"`
  的硬跳转；在生产 frontend 镜像中会 404。Phase 1（前端同事负责）会用 Vue 重写
  庭审页后删除该跳转与 mock-court 目录。
- **MinIO presigned URL 在容器化部署下的浏览器可达性**：容器内 backend 使用
  `minio:9000` 生成 presigned URL，浏览器无法解析 `minio` 主机名。
  本地开发模式（backend 跑在宿主机，`.env` 中 `MINIO_ENDPOINT=localhost:9000`）
  不受影响。生产部署需通过统一域名 / nginx 反代 MinIO 来解决。
- **`/ws/trial` 无鉴权**：Phase 0 未做 token 校验（PLAN 列为 backlog）。

---

## 七、故障排查

```bash
# 查看所有服务状态
docker compose ps

# 查看某服务日志
docker compose logs -f backend
docker compose logs -f frontend

# 进入容器调试
docker compose exec backend bash
docker compose exec postgres psql -U postgres court_system

# 端口占用排查（宿主机）
ss -tlnp | grep -E ':(80|8000|5432|9000|9001)\s'
```

### 后端无法连接数据库

```bash
docker compose ps postgres          # 确保healthy
docker compose exec backend curl -v postgres:5432   # 容器内连通性
docker compose logs postgres
```

### 前端 80 端口被占用

修改 `docker-compose.yml`：`ports: - "8080:80"`，然后访问 http://localhost:8080

### 想回退到旧的 all-in-one 镜像

旧 Dockerfile / supervisord / entrypoint 已标记为 DEPRECATED，保留一个版本周期。
构建命令：

```bash
docker build -t digital-court:all-in-one -f Dockerfile .
docker run -d -p 80:80 -p 9000:9000 -p 9001:9001 digital-court:all-in-one
```

Phase 1（React 删除）完成后会彻底移除这些文件。
