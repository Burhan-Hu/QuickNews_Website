# QuickNews 全栈部署 Dockerfile
# 前端构建 + Flask 后端一体部署

# ==================== 阶段 1：构建前端 ====================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# 复制前端依赖文件
COPY app/package*.json ./

# 安装依赖
RUN npm ci --only=production

# 复制前端源码
COPY app/ ./

# 构建前端（输出到 dist 目录）
RUN npm run build

# ==================== 阶段 2：Python 后端 ====================
FROM python:3.11-slim AS backend

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 复制 Python 依赖
COPY news_dashboard/requirements.txt ./

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY news_dashboard/ ./

# ==================== 阶段 3：最终镜像 ====================
FROM python:3.11-slim

WORKDIR /app

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制 Python 包
COPY --from=backend /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend /usr/local/bin /usr/local/bin

# 复制后端代码
COPY news_dashboard/ ./

# 复制构建好的前端静态文件到 Flask 静态目录
COPY --from=frontend-builder /app/frontend/dist ./static

# 创建启动脚本
RUN echo '#!/bin/bash\n\
# 设置环境变量\n\
export PYTHONPATH=/app:$PYTHONPATH\n\
\n\
# 启动 Flask 应用（生产环境使用 gunicorn）\n\
if [ "$FLASK_ENV" = "development" ]; then\n\
    python ir/xml_api.py\n\
else\n\
    # 生产环境：使用 gunicorn，4个 worker，绑定 0.0.0.0:5000\n\
    gunicorn -w 2 -b 0.0.0.0:5000 --timeout 120 --access-logfile - --error-logfile - "ir.xml_api:create_app()"\n\
fi' > /app/start.sh && chmod +x /app/start.sh

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# 启动命令
CMD ["/app/start.sh"]
