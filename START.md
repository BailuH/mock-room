# 启动指南

本文档说明如何启动数字法庭系统的所有服务。

## 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| PostgreSQL | 5432 | 数据库 |
| MinIO API | 9000 | 对象存储 API |
| MinIO Console | 9001 | MinIO 管理界面 |
| debate_mfxb2 (后端) | 8000 | FastAPI 后端 |
| court_vue3 (前端) | 8083 | Vue3 前端 |

---

## 一、启动 Docker 服务 (PostgreSQL + MinIO)

```bash
cd /home/bailu/codebase
docker-compose up -d
```

### 验证 Docker 服务状态

```bash
# 查看容器状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 停止 Docker 服务

```bash
docker-compose down

# 停止并删除数据卷（慎用，会清空所有数据）
docker-compose down -v
```

---

## 二、初始化 MinIO

首次启动需要创建存储桶：

### 方式一：通过 Web Console

1. 访问 http://localhost:9001
2. 登录（用户名: `minioadmin`，密码: `minio123`）
3. 点击右侧 "+Create Bucket" 按钮
4. 输入桶名: `court-cases`
5. 点击 "Create Bucket"

### 方式二：通过命令行

```bash
# 安装 MinIO 客户端
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc
sudo mv mc /usr/local/bin/

# 配置连接
mc alias set local http://localhost:9000 minioadmin minio123

# 创建桶
mc mb local/court-cases

# 设置为公开读取（可选）
mc anonymous set download local/court-cases
```

---

## 三、启动后端

```bash
cd /home/bailu/codebase/debate_mfxb2
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

后端启动成功后，会看到：
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## 四、启动前端

### 首次启动（安装依赖）

```bash
cd /home/bailu/codebase/court_vue3
npm install
```

### 启动开发服务器

```bash
npm run serve
```

前端启动成功后，会看到：
```
INFO  Starting development server...
INFO  App running at:
  - Local:   http://localhost:8083/
  - Network: http://192.168.x.x:8083/
```

---

## 五、访问应用

| 服务 | 地址 |
|------|------|
| 前端应用 | http://localhost:8083 |
| 后端 API | http://localhost:8000 |
| API 文档 | http://localhost:8000/docs |
| MinIO Console | http://localhost:9001 |

---

## 六、完整启动流程（三个终端）

### 终端 1 - Docker 服务
```bash
cd /home/bailu/codebase
docker-compose up -d
```

### 终端 2 - 后端
```bash
cd /home/bailu/codebase/debate_mfxb2
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

### 终端 3 - 前端
```bash
cd /home/bailu/codebase/court_vue3
npm run serve
```

---

## 七、账号信息

| 服务 | 用户名 | 密码 | 用途 |
|------|--------|------|------|
| PostgreSQL | postgres | court123 | 数据库连接 |
| MinIO Console | minioadmin | minio123 | 文件存储管理 |

**注意**: 前端登录使用手机号作为用户名，密码在前端注册时自行设置。

---

## 八、故障排查

### 后端无法连接数据库

```bash
# 检查 Docker 容器状态
docker-compose ps

# 确保 PostgreSQL 容器正在运行
# 如果没有运行，执行：docker-compose up -d
```

### 前端无法连接后端

1. 确认后端已启动（访问 http://localhost:8000/health）
2. 确认后端端口 8000 未被占用
3. 检查浏览器控制台是否有 CORS 错误

### 文件上传失败

1. 确认 MinIO 正在运行（访问 http://localhost:9001）
2. 确认已创建 `court-cases` 桶
3. 检查 MinIO 连接配置（.env 文件）

---

## 九、停止所有服务

```bash
# 停止前端（Ctrl+C）

# 停止后端（Ctrl+C）

# 停止 Docker 服务
cd /home/bailu/codebase
docker-compose down
```
