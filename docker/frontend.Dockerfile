# ============================================================
# 前端镜像：court_vue3 构建 + nginx:alpine 静态托管
#   - 多阶段构建：node 编译 -> nginx 运行
#   - nginx 同域反代 /api、/ws 到 backend:8000
#   - court_vue3 同域 baseURL 设为空串，API 请求全部走 nginx 反代
# ============================================================
# 基础镜像可通过构建参数覆盖，便于网络受限环境使用镜像源：
#   docker build -f docker/frontend.Dockerfile \
#     --build-arg NODE_IMAGE=docker.m.daocloud.io/library/node:20-bookworm-slim \
#     --build-arg NGINX_IMAGE=docker.m.daocloud.io/library/nginx:alpine \
#     -t digital-court:frontend ./court_vue3
# ============================================================

# ------------------------------------------------------------
# Stage 1: 构建 court_vue3
# ------------------------------------------------------------
ARG NODE_IMAGE=node:20-bookworm-slim
FROM ${NODE_IMAGE} AS frontend-build
WORKDIR /build

# 国内构建加速；境外服务器同样可用
RUN npm config set registry https://registry.npmmirror.com

# build context = 仓库根，故 court_vue3/* 路径前缀必须保留
COPY court_vue3/package.json court_vue3/package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY court_vue3/ ./

# 同域反代：baseURL 设为空串，API 请求走 nginx 反代，不再写死 localhost:8000
ARG VUE_APP_API_BASE_URL=""
ENV VUE_APP_API_BASE_URL=${VUE_APP_API_BASE_URL}
ENV NODE_OPTIONS=--max-old-space-size=4096

RUN npm run build

# ------------------------------------------------------------
# Stage 2: nginx 运行时
# ------------------------------------------------------------
ARG NGINX_IMAGE=nginx:alpine
FROM ${NGINX_IMAGE} AS runtime

# nginx 配置从仓库根 docker/nginx.conf 拷入
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

# 移除 nginx 默认.conf 避免冲突
RUN rm -f /etc/nginx/conf.d/default.conf.bak

COPY --from=frontend-build /build/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -qO- http://127.0.0.1/ >/dev/null 2>&1 || exit 1

CMD ["nginx", "-g", "daemon off;"]
