# 腾讯云部署指南

## 一、部署方案选择

### 方案 A：Docker Compose 一键部署（推荐）
适合快速部署，所有服务容器化，易于维护。

### 方案 B：手动部署 + Nginx
适合生产环境，前后端分离部署，性能更好。

---

## 二、准备工作

### 1. 购买腾讯云服务器 (CVM)

- **推荐配置**：2核4G 或更高
- **系统**：Ubuntu 22.04 LTS / CentOS 8
- **带宽**：≥5Mbps
- **开放端口**：80, 443, 8000, 9000, 9001 (安全组配置)

### 2. 准备部署包

在你的本地机器执行：

```bash
# 进入项目目录
cd /home/bailu/codebase/mock-room

# 1. 打包前端（构建生产环境代码）
cd court_vue3
npm install
npm run build
# 生成 dist/ 目录

# 2. 后端准备（如果使用 Docker 部署可跳过）
cd ../debate_mfxb2
# 确保依赖安装
pip install -r requirements.txt  # 或使用 uv sync
```

---

## 三、方案 A：Docker Compose 部署

### 步骤 1：打包上传项目

```bash
# 在本地打包项目（排除 node_modules 等）
cd /home/bailu/codebase/mock-room
tar -czvf court-system.tar.gz \
  --exclude='node_modules' \
  --exclude='.venv' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.git' \
  court_vue3/dist \
  debate_mfxb2 \
  docker-compose.yml

# 上传到服务器
scp court-system.tar.gz root@你的服务器IP:/opt/
```

### 步骤 2：服务器端配置

```bash
# 连接服务器
ssh root@你的服务器IP

# 安装 Docker 和 Docker Compose
curl -fsSL https://get.docker.com | sh
systemctl enable docker
systemctl start docker

# 解压项目
cd /opt
mkdir -p court-system && cd court-system
tar -xzvf ../court-system.tar.gz
```

创建生产环境 docker-compose.prod.yml：

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: court_db
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: 你的强密码
      POSTGRES_DB: court_system
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - court_network
    restart: unless-stopped

  minio:
    image: minio/minio:latest
    container_name: court_storage
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: 你的强密码
    volumes:
      - minio_data:/data
    networks:
      - court_network
    restart: unless-stopped

  backend:
    build:
      context: ./debate_mfxb2
      dockerfile: Dockerfile
    container_name: court_backend
    environment:
      - DATABASE_URL=postgresql://postgres:你的强密码@postgres:5432/court_system
      - MINIO_ENDPOINT=minio:9000
    ports:
      - "8000:8000"
    depends_on:
      - postgres
    networks:
      - court_network
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    container_name: court_nginx
    ports:
      - "80:80"
    volumes:
      - ./court_vue3/dist:/usr/share/nginx/html:ro
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - backend
    networks:
      - court_network
    restart: unless-stopped

volumes:
  postgres_data:
  minio_data:

networks:
  court_network:
    driver: bridge
```

### 步骤 3：创建后端 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装 uv
RUN pip install uv

# 复制项目文件
COPY pyproject.toml uv.lock ./
COPY src ./src

# 安装依赖
RUN uv sync

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uv", "run", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 步骤 4：配置 Nginx

```nginx
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    # Gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript;

    # 后端 API 代理
    upstream backend {
        server backend:8000;
    }

    server {
        listen 80;
        server_name _;

        # 前端静态文件
        location / {
            root /usr/share/nginx/html;
            try_files $uri $uri/ /index.html;
        }

        # API 代理
        location /api/ {
            proxy_pass http://backend/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_cache_bypass $http_upgrade;
        }
    }
}
```

### 步骤 5：启动服务

```bash
cd /opt/court-system

# 构建并启动
docker-compose -f docker-compose.prod.yml up -d --build

# 查看状态
docker-compose -f docker-compose.prod.yml ps
```

---

## 四、快速部署脚本

我为你准备了一键部署脚本，保存在 `deploy/` 目录下：

1. **build.sh** - 本地构建打包
2. **deploy.sh** - 服务器部署脚本

---

## 五、访问验证

| 访问地址 | 说明 |
|---------|------|
| `http://服务器IP` | 前端页面 |
| `http://服务器IP/api/docs` | API 文档 |
| `http://服务器IP:8000/health` | 后端健康检查 |

---

## 六、配置 HTTPS（可选）

```bash
# 安装 Certbot
apt install -y certbot python3-certbot-nginx

# 申请证书
certbot --nginx -d your-domain.com
```
