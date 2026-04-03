#!/bin/bash
# QuickNews 部署准备脚本
# 用于生成本地测试或 ClawCloud 部署所需的文件

set -e

echo "=========================================="
echo "QuickNews 部署准备脚本"
echo "=========================================="

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查命令
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

echo ""
echo "🔍 检查环境..."

# 检查 Node.js
if command_exists node; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓${NC} Node.js 已安装: $NODE_VERSION"
else
    echo -e "${RED}✗${NC} Node.js 未安装，请先安装 Node.js 18+"
    exit 1
fi

# 检查 npm
if command_exists npm; then
    NPM_VERSION=$(npm --version)
    echo -e "${GREEN}✓${NC} npm 已安装: $NPM_VERSION"
else
    echo -e "${RED}✗${NC} npm 未安装"
    exit 1
fi

# 检查 Docker（可选）
if command_exists docker; then
    DOCKER_VERSION=$(docker --version)
    echo -e "${GREEN}✓${NC} Docker 已安装: $DOCKER_VERSION"
    HAS_DOCKER=true
else
    echo -e "${YELLOW}⚠${NC} Docker 未安装（可选，用于本地测试）"
    HAS_DOCKER=false
fi

echo ""
echo "📦 步骤 1/4: 安装前端依赖..."
cd app
if [ ! -d "node_modules" ]; then
    npm install
else
    echo "node_modules 已存在，跳过安装"
fi

echo ""
echo "🏗️ 步骤 2/4: 构建前端..."
npm run build

if [ ! -d "dist" ]; then
    echo -e "${RED}✗${NC} 前端构建失败，dist 目录不存在"
    exit 1
fi

echo -e "${GREEN}✓${NC} 前端构建成功"
cd ..

echo ""
echo "📋 步骤 3/4: 检查配置文件..."

# 检查 Dockerfile
if [ ! -f "Dockerfile" ]; then
    echo -e "${RED}✗${NC} Dockerfile 不存在"
    exit 1
fi
echo -e "${GREEN}✓${NC} Dockerfile 存在"

# 检查 requirements.txt
if [ ! -f "news_dashboard/requirements.txt" ]; then
    echo -e "${RED}✗${NC} requirements.txt 不存在"
    exit 1
fi
echo -e "${GREEN}✓${NC} requirements.txt 存在"

# 检查 .dockerignore
if [ ! -f ".dockerignore" ]; then
    echo -e "${YELLOW}⚠${NC} .dockerignore 不存在"
else
    echo -e "${GREEN}✓${NC} .dockerignore 存在"
fi

echo ""
echo "🐳 步骤 4/4: 测试 Docker 构建..."
if [ "$HAS_DOCKER" = true ]; then
    echo "正在构建 Docker 镜像（这可能需要几分钟）..."
    docker build -t quicknews:local-test .
    echo -e "${GREEN}✓${NC} Docker 镜像构建成功"
    
    echo ""
    echo "💡 本地测试运行命令："
    echo "  docker run -p 5000:5000 \\"
    echo "    -e DB_HOST=your-db-host \\"
    echo "    -e DB_USER=your-db-user \\"
    echo "    -e DB_PASSWORD=your-db-password \\"
    echo "    -e DB_NAME=your-db-name \\"
    echo "    quicknews:local-test"
else
    echo -e "${YELLOW}⚠${NC} 跳过 Docker 测试（Docker 未安装）"
fi

echo ""
echo "=========================================="
echo "✅ 部署准备完成！"
echo "=========================================="
echo ""
echo "下一步操作："
echo ""
echo "1. 本地测试（可选）："
if [ "$HAS_DOCKER" = true ]; then
    echo "   docker run -p 5000:5000 quicknews:local-test"
fi

echo ""
echo "2. 部署到 ClawCloud："
echo "   a. 访问 https://console.run.claw.cloud"
echo "   b. 使用 GitHub 登录"
echo "   c. 创建 App，选择 'Deploy from Dockerfile'"
echo "   d. 配置环境变量（数据库连接信息）"
echo "   e. 部署！"

echo ""
echo "3. 详细部署文档："
echo "   查看 DEPLOY.md 获取完整指南"
echo ""
echo "=========================================="
