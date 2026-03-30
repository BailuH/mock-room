#!/bin/bash
# ============================================
# 数字法庭系统 - 本地构建打包脚本
# 使用方式: ./build.sh
# ============================================

set -e

echo "🚀 开始构建数字法庭系统..."

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_DIR="$PROJECT_ROOT/deploy/build"
VERSION=$(date +%Y%m%d_%H%M%S)

echo -e "${YELLOW}📁 项目目录: $PROJECT_ROOT${NC}"
echo -e "${YELLOW}📦 版本号: $VERSION${NC}"

# 清理并创建构建目录
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# ============================================
# 1. 构建前端
# ============================================
echo -e "${GREEN}🔨 步骤 1/3: 构建前端...${NC}"

cd "$PROJECT_ROOT/court_vue3"

# 检查 node_modules
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠️  未找到 node_modules，正在安装依赖...${NC}"
    npm install
fi

# 构建生产环境
npm run build

# 复制构建产物
mkdir -p "$BUILD_DIR/court_vue3"
cp -r dist "$BUILD_DIR/court_vue3/"

echo -e "${GREEN}✅ 前端构建完成${NC}"

# ============================================
# 2. 准备后端
# ============================================
echo -e "${GREEN}🔨 步骤 2/3: 准备后端...${NC}"

cd "$PROJECT_ROOT"

# 复制后端代码
mkdir -p "$BUILD_DIR/debate_mfxb2"
cp -r debate_mfxb2/src "$BUILD_DIR/debate_mfxb2/"
cp debate_mfxb2/pyproject.toml "$BUILD_DIR/debate_mfxb2/"
cp debate_mfxb2/uv.lock "$BUILD_DIR/debate_mfxb2/"

# 创建后端 Dockerfile
cat > "$BUILD_DIR/debate_mfxb2/Dockerfile" << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv
RUN pip install --no-cache-dir uv

# 复制依赖文件
COPY pyproject.toml uv.lock ./

# 复制源代码
COPY src ./src

# 安装 Python 依赖
RUN uv sync

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD uv run python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# 启动命令
CMD ["uv", "run", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

echo -e "${GREEN}✅ 后端准备完成${NC}"

# ============================================
# 3. 创建部署文件
# ============================================
echo -e "${GREEN}🔨 步骤 3/3: 创建部署文件...${NC}"

# 复制 docker-compose
cp "$PROJECT_ROOT/docker-compose.yml" "$BUILD_DIR/"

# 创建生产环境 docker-compose
cat > "$BUILD_DIR/docker-compose.prod.yml" << 'EOF'
version: '3.8'

services:
  # PostgreSQL 数据库
  postgres:
    image: postgres:16-alpine
    container_name: court_db
    environment:
      POSTGRES_USER: ${DB_USER:-postgres}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-court123}
      POSTGRES_DB: court_system
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - court_network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-postgres}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # MinIO 对象存储
  minio:
    image: minio/minio:latest
    container_name: court_storage
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_USER:-minioadmin}
      MINIO_ROOT_PASSWORD: ${MINIO_PASSWORD:-minio123}
    volumes:
      - minio_data:/data
    networks:
      - court_network
    restart: unless-stopped

  # 后端服务
  backend:
    build:
      context: ./debate_mfxb2
      dockerfile: Dockerfile
    container_name: court_backend
    environment:
      - DATABASE_URL=postgresql://${DB_USER:-postgres}:${DB_PASSWORD:-court123}@postgres:5432/court_system
      - MINIO_ENDPOINT=minio:9000
      - MINIO_ACCESS_KEY=${MINIO_USER:-minioadmin}
      - MINIO_SECRET_KEY=${MINIO_PASSWORD:-minio123}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - LANGCHAIN_API_KEY=${LANGCHAIN_API_KEY}
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - court_network
    restart: unless-stopped

  # Nginx 前端 + 反向代理
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
EOF

# 创建 Nginx 配置
cat > "$BUILD_DIR/nginx.conf" << 'EOF'
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    # 日志
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    # Gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml;

    # 后端服务
    upstream backend {
        server backend:8000;
    }

    server {
        listen 80;
        server_name _;

        # 安全响应头
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;

        # 前端静态文件
        location / {
            root /usr/share/nginx/html;
            try_files $uri $uri/ /index.html;
            index index.html;
        }

        # 静态资源缓存
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
            root /usr/share/nginx/html;
            expires 1y;
            add_header Cache-Control "public, immutable";
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
            proxy_read_timeout 86400;
        }

        # WebSocket 支持
        location /ws/ {
            proxy_pass http://backend/ws/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_read_timeout 86400;
        }
    }
}
EOF

# 创建环境变量模板
cat > "$BUILD_DIR/.env.example" << 'EOF'
# 数据库配置
DB_USER=postgres
DB_PASSWORD=你的强密码

# MinIO 配置
MINIO_USER=minioadmin
MINIO_PASSWORD=你的强密码

# OpenAI API Key
OPENAI_API_KEY=sk-你的密钥

# LangSmith (可选)
LANGCHAIN_API_KEY=你的密钥
EOF

# 创建服务器部署脚本
cat > "$BUILD_DIR/deploy.sh" << 'EOF'
#!/bin/bash
# 服务器端部署脚本

set -e

echo "🚀 开始部署数字法庭系统..."

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "📦 安装 Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
fi

# 检查 Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "📦 安装 Docker Compose..."
    pip3 install docker-compose || apt install -y docker-compose-plugin
fi

# 加载环境变量
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | xargs)
fi

# 停止旧服务
echo "🛑 停止旧服务..."
docker-compose -f docker-compose.prod.yml down 2>/dev/null || true

# 构建并启动
echo "🔨 构建并启动服务..."
docker-compose -f docker-compose.prod.yml up -d --build

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查状态
echo "✅ 检查服务状态..."
docker-compose -f docker-compose.prod.yml ps

# 初始化 MinIO Bucket
echo "📦 初始化 MinIO..."
docker exec court_storage mc alias set local http://localhost:9000 ${MINIO_USER:-minioadmin} ${MINIO_PASSWORD:-minio123} 2>/dev/null || true
docker exec court_storage mc mb local/court-cases 2>/dev/null || echo "Bucket 可能已存在"

echo "🎉 部署完成！"
echo "📱 访问地址: http://$(curl -s ifconfig.me)"
echo "📚 API 文档: http://$(curl -s ifconfig.me)/api/docs"
EOF
chmod +x "$BUILD_DIR/deploy.sh"

# ============================================
# 4. 打包
# ============================================
echo -e "${GREEN}📦 打包部署文件...${NC}"

cd "$PROJECT_ROOT/deploy"
tar -czvf "court-system-${VERSION}.tar.gz" -C "$BUILD_DIR" .

echo -e "${GREEN}✅ 构建完成！${NC}"
echo ""
echo -e "${YELLOW}📦 部署包: deploy/court-system-${VERSION}.tar.gz${NC}"
echo ""
echo "🚀 上传到服务器并部署:"
echo "   scp deploy/court-system-${VERSION}.tar.gz root@你的服务器IP:/opt/"
echo ""
echo "📖 详细说明请查看: deploy/tencent-deploy-guide.md"
