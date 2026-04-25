#!/bin/bash
# QuickNews 阿里云ECS一键部署脚本
# 使用前请确保：1) 已领取ECS  2) 安全组已开80端口  3) Aiven已加ECS IP白名单

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "=========================================="
echo "  QuickNews 阿里云ECS一键部署脚本"
echo "=========================================="

# 检查root权限
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}✗ 请使用 root 权限运行: sudo bash deploy_aliyun.sh${NC}"
    exit 1
fi

# 交互式输入配置
echo ""
echo "📋 请输入配置信息（直接回车使用默认值）："
read -p "GitHub仓库地址 [默认: https://github.com/Burhan-Hu/QuickNews_Website.git]: " REPO_URL
REPO_URL=${REPO_URL:-https://github.com/Burhan-Hu/QuickNews_Website.git}

read -p "Aiven DB Host: " DB_HOST
read -p "Aiven DB Port [3306]: " DB_PORT
DB_PORT=${DB_PORT:-3306}
read -p "Aiven DB User: " DB_USER
read -s -p "Aiven DB Password: " DB_PASSWORD
echo
read -p "Aiven DB Name [quicknews]: " DB_NAME
DB_NAME=${DB_NAME:-quicknews}
read -p "ECS公网IP: " ECS_IP

INSTALL_DIR="/opt/qknews"

echo ""
echo "🚀 开始部署..."

# 1. 更新系统
echo -e "${YELLOW}[1/10] 更新系统...${NC}"
apt-get update && apt-get upgrade -y

# 2. 安装基础依赖
echo -e "${YELLOW}[2/10] 安装基础依赖...${NC}"
apt-get install -y git nginx curl software-properties-common build-essential

# 3. 安装Python
echo -e "${YELLOW}[3/10] 安装Python环境...${NC}"
apt-get install -y python3 python3-pip python3-venv

# 4. 安装Node.js 20
echo -e "${YELLOW}[4/10] 安装Node.js...${NC}"
if ! command -v node &> /dev/null || [ "$(node -v | cut -d'v' -f2 | cut -d'.' -f1)" -lt 18 ]; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
fi
NODE_VERSION=$(node --version)
echo -e "${GREEN}✓ Node.js $NODE_VERSION 已就绪${NC}"

# 5. 克隆代码
echo -e "${YELLOW}[5/10] 克隆代码...${NC}"
if [ -d "$INSTALL_DIR" ]; then
    echo "目录已存在，先备份..."
    mv "$INSTALL_DIR" "${INSTALL_DIR}.bak.$(date +%Y%m%d%H%M%S)"
fi
git clone "$REPO_URL" "$INSTALL_DIR"
cd "$INSTALL_DIR"

# 6. 创建环境变量
echo -e "${YELLOW}[6/10] 配置环境变量...${NC}"
cat > news_dashboard/.env << EOF
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_NAME=$DB_NAME
CORS_ORIGINS=http://$ECS_IP
EOF
chmod 600 news_dashboard/.env
echo -e "${GREEN}✓ 环境变量已写入 news_dashboard/.env${NC}"

# 7. 安装Python依赖
echo -e "${YELLOW}[7/10] 安装Python依赖...${NC}"
cd news_dashboard
pip3 install -r requirements.txt
cd ..

# 8. 构建前端
echo -e "${YELLOW}[8/10] 构建前端...${NC}"
cd app
npm config set registry https://registry.npmmirror.com
npm install
cat > .env.production << EOF
VITE_API_BASE_URL=http://$ECS_IP/api
EOF
npm run build
cd ..

# 9. 配置Nginx
echo -e "${YELLOW}[9/10] 配置Nginx...${NC}"
cat > /etc/nginx/sites-available/qknews << EOF
server {
    listen 80;
    server_name _;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    location / {
        root $INSTALL_DIR/app/dist;
        index index.html;
        try_files \$uri \$uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    location /sru {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }

    location /health {
        proxy_pass http://127.0.0.1:5000;
    }
}
EOF

rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/qknews /etc/nginx/sites-enabled/qknews
nginx -t
systemctl restart nginx
systemctl enable nginx
echo -e "${GREEN}✓ Nginx 配置完成${NC}"

# 10. 配置Systemd
echo -e "${YELLOW}[10/10] 配置Systemd服务...${NC}"

# API服务
cat > /etc/systemd/system/qknews-api.service << EOF
[Unit]
Description=QuickNews API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR/news_dashboard
Environment=PYTHONUNBUFFERED=1
EnvironmentFile=$INSTALL_DIR/news_dashboard/.env
ExecStart=/usr/local/bin/gunicorn -w 2 -b 127.0.0.1:5000 wsgi:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 爬虫服务（每20分钟）
cat > /etc/systemd/system/qknews-crawler.service << EOF
[Unit]
Description=QuickNews Crawler
After=network.target

[Service]
Type=oneshot
User=root
WorkingDirectory=$INSTALL_DIR/news_dashboard
EnvironmentFile=$INSTALL_DIR/news_dashboard/.env
ExecStart=/usr/bin/python3 $INSTALL_DIR/news_dashboard/cron_fetch.py
EOF

cat > /etc/systemd/system/qknews-crawler.timer << EOF
[Unit]
Description=Run QuickNews Crawler every 20 minutes

[Timer]
OnCalendar=*:0/20
Persistent=true

[Install]
WantedBy=timers.target
EOF

# 话题更新服务（每小时）
cat > /etc/systemd/system/qknews-topics.service << EOF
[Unit]
Description=QuickNews Topic Updater
After=network.target

[Service]
Type=oneshot
User=root
WorkingDirectory=$INSTALL_DIR/news_dashboard
EnvironmentFile=$INSTALL_DIR/news_dashboard/.env
ExecStart=/usr/bin/python3 $INSTALL_DIR/news_dashboard/cron_topics.py
EOF

cat > /etc/systemd/system/qknews-topics.timer << EOF
[Unit]
Description=Run QuickNews Topic Updater hourly

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable --now qknews-api
systemctl enable --now qknews-crawler.timer
systemctl enable --now qknews-topics.timer

echo ""
echo "=========================================="
echo -e "${GREEN}✅ 部署完成！${NC}"
echo "=========================================="
echo ""
echo "🌐 访问地址: http://$ECS_IP"
echo "💚 健康检查: http://$ECS_IP/health"
echo ""
echo "📊 常用命令:"
echo "  查看API日志:      journalctl -u qknews-api -f"
echo "  查看爬虫定时器:   systemctl list-timers"
echo "  手动运行爬虫:     systemctl start qknews-crawler"
echo "  重启API:          systemctl restart qknews-api"
echo "  重启Nginx:        systemctl restart nginx"
echo ""
echo "⚠️  重要提醒:"
echo "  1. 请确保 Aiven 数据库已允许 $ECS_IP 访问"
echo "  2. 请确保阿里云安全组已开放 80 端口"
echo "  3. 免费试用到期前请及时备份或续费"
echo "=========================================="
