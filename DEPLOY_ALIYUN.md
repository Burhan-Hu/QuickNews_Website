# QuickNews 阿里云ECS免费试用部署指南

> 适用于阿里云"个人免费试用"ECS实例（1核2G/1M带宽，免费1-3个月）

## 架构说明

```
用户浏览器
    │
    ▼
阿里云ECS (公网IP:80)
    │
    ├── Nginx
    │   ├── /          → 前端静态文件 (app/dist)
    │   ├── /api/*     → Gunicorn (127.0.0.1:5000)
    │   ├── /sru       → Gunicorn (127.0.0.1:5000)
    │   └── /health    → Gunicorn (127.0.0.1:5000)
    │
    ├── Gunicorn (Flask后端，2个worker)
    │
    └── Systemd Timer
        ├── 每20分钟 → 爬虫抓取新闻 (cron_fetch.py)
        └── 每小时   → 更新热点话题 (cron_topics.py)
    
外部服务: Aiven Cloud MySQL (数据库)
```

**不需要在ECS上安装MySQL**，数据库继续使用Aiven，ECS只跑应用代码。

---

## 前置准备（3步，必须先做）

### 步骤1：领取阿里云ECS免费试用

1. 访问 [阿里云免费试用中心](https://free.aliyun.com/)
2. 找到 **"云服务器 ECS"** → 选择 **"个人免费试用"**
3. 配置选择：
   - **地域**：选离你近的（如"华南1(深圳)"或"华东1(杭州)")
   - **操作系统**：**Ubuntu 22.04 64位**（或 Alibaba Cloud Linux 3）
   - **实例规格**：默认的即可（通常是 `ecs.t6-c2m1` 或 `ecs.n4`）
   - **带宽**：1Mbps（默认）
4. 点击"立即试用"，等待实例创建完成（约1-2分钟）
5. **记录公网IP**：在ECS控制台 → 实例列表 → 找到你的实例，复制"公网IP"

### 步骤2：配置安全组（开放80端口）

1. 在ECS控制台 → 点击实例名 → **安全组** → **配置规则**
2. 点击 **"入方向"** → **"手动添加"**
3. 添加一条规则：
   - 授权策略：**允许**
   - 协议类型：**自定义TCP**
   - 端口范围：**80/80**
   - 授权对象：**0.0.0.0/0**
   - 描述：HTTP访问
4. 确认已有 **22端口**（SSH）的规则，没有的话也加上

### 步骤3：Aiven数据库添加ECS IP白名单

1. 登录 [Aiven Console](https://console.aiven.io/)
2. 进入你的MySQL服务 → **Settings** → **IP Allowlist**
3. 点击 **"Add IP Address"**
4. 填入你的 **ECS公网IP**，点击保存
5. 等待约30秒生效

---

## 部署步骤

### 方法一：一键脚本（推荐，10分钟完成）

#### 1. 连接到你的ECS

**方式A：阿里云控制台网页终端（最简单）**
- 进入ECS控制台 → 点击实例 → **远程连接** → **Workbench远程连接** → 输入root密码登录

**方式B：Windows Terminal / PowerShell**
```powershell
ssh root@你的ECS公网IP
# 输入root密码（首次连接可能需要输入yes确认）
```

**方式C：PuTTY/Xshell**
- Host Name: `root@你的ECS公网IP`
- Port: `22`
- 连接类型: SSH

#### 2. 下载并运行部署脚本

```bash
# 进入root目录
cd /root

# 下载脚本（如果git clone不行，可以手动复制粘贴）
curl -O https://raw.githubusercontent.com/Burhan-Hu/QuickNews_Website/main/deploy_aliyun.sh

# 或者直接用git把项目拉下来，脚本就在里面
git clone https://github.com/Burhan-Hu/QuickNews_Website.git /opt/qknews
cd /opt/qknews
chmod +x deploy_aliyun.sh
bash deploy_aliyun.sh
```

**脚本会交互式询问以下信息：**
- GitHub仓库地址（直接回车用默认）
- Aiven DB Host（如 `your-db.aivencloud.com`）
- Aiven DB Port（直接回车用3306）
- Aiven DB User
- Aiven DB Password（输入时不显示，回车确认）
- Aiven DB Name（直接回车用quicknews）
- ECS公网IP

输入完成后，脚本自动完成全部部署，约5-10分钟。

### 方法二：手动分步部署

如果一键脚本遇到问题，可以手动执行：

```bash
# 1. 更新系统
apt update && apt upgrade -y

# 2. 安装依赖
apt install -y git nginx python3 python3-pip curl

# 3. 安装Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs

# 4. 克隆代码
cd /opt
git clone https://github.com/Burhan-Hu/QuickNews_Website.git qknews
cd qknews

# 5. 创建环境变量文件
cat > news_dashboard/.env << 'EOF'
DB_HOST=你的Aiven主机
DB_PORT=3306
DB_USER=你的用户名
DB_PASSWORD=你的密码
DB_NAME=quicknews
CORS_ORIGINS=http://你的ECS公网IP
EOF

# 6. 安装Python依赖
cd news_dashboard
pip3 install -r requirements.txt
cd ..

# 7. 构建前端
cd app
npm config set registry https://registry.npmmirror.com
npm install
echo "VITE_API_BASE_URL=http://你的ECS公网IP/api" > .env.production
npm run build
cd ..

# 8. 配置Nginx（见deploy_aliyun.sh中第9步的nginx配置内容）
# ... 手动编辑 /etc/nginx/sites-available/qknews

# 9. 配置Systemd（见deploy_aliyun.sh中第10步的systemd配置内容）
# ... 手动创建3个service和2个timer文件

# 10. 启动服务
systemctl restart nginx
systemctl enable --now qknews-api
systemctl enable --now qknews-crawler.timer
systemctl enable --now qknews-topics.timer
```

---

## 验证部署

部署完成后，在浏览器访问：

| 地址 | 用途 |
|------|------|
| `http://你的ECS公网IP` | 前端首页 |
| `http://你的ECS公网IP/health` | 后端健康检查 |
| `http://你的ECS公网IP/api/hot-topics` | 热点话题API |

### 检查服务状态

```bash
# 查看所有定时任务
systemctl list-timers

# 查看API是否正常运行
systemctl status qknews-api

# 查看API实时日志
journalctl -u qknews-api -f

# 查看爬虫日志
journalctl -u qknews-crawler -f

# 手动触发一次爬虫（测试用）
systemctl start qknews-crawler
journalctl -u qknews-crawler -f
```

---

## 常用运维命令

```bash
# 重启API服务
systemctl restart qknews-api

# 重启Nginx
systemctl restart nginx

# 查看Nginx错误日志
tail -f /var/log/nginx/error.log

# 更新代码后重新部署
cd /opt/qknews && git pull
# 然后重新运行 deploy_aliyun.sh，或手动重建前端、重启服务

# 查看系统资源占用
top
```

---

## 注意事项

### 1. 免费试用到期
阿里云ECS免费试用通常 **1-3个月**。
- **到期前**：备份数据（主要是Aiven里的数据库，代码在GitHub上）
- **到期后**：可以购买按量付费（约0.1-0.2元/小时）或包年包月（约30-50元/月）

### 2. 带宽限制
免费试用ECS是 **1Mbps带宽**，约 **128KB/s**。
- 首次加载前端可能稍慢（打包后约几百KB到几MB）
- 日常API调用没问题
- 如需更快，可后续升级带宽

### 3. 安全问题
- 脚本中 `.env` 文件权限设为 `600`（仅root可读）
- 建议后续配置HTTPS（阿里云有免费SSL证书）
- 建议修改SSH默认端口或配置密钥登录（防止暴力破解）

### 4. 数据库连接
- ECS通过公网连接Aiven，延迟约30-100ms
- 如果Aiven连接不稳定，检查白名单是否包含ECS当前IP（ECS重启后IP可能变化）

---

## 故障排查

### 问题1：浏览器访问IP显示空白或502

```bash
# 检查Nginx是否运行
systemctl status nginx

# 检查API是否运行
systemctl status qknews-api

# 查看Nginx错误日志
cat /var/log/nginx/error.log

# 手动测试API
curl http://127.0.0.1:5000/health
```

### 问题2：爬虫不运行

```bash
# 检查定时器状态
systemctl status qknews-crawler.timer
systemctl list-timers

# 手动运行看报错
systemctl start qknews-crawler
journalctl -u qknews-crawler -e
```

### 问题3：数据库连接失败

```bash
# 测试数据库连接
cd /opt/qknews/news_dashboard
python3 -c "from config.db_config import test_connection; test_connection()"

# 检查.env文件是否正确
cat /opt/qknews/news_dashboard/.env

# 确认Aiven白名单已添加ECS公网IP
```

### 问题4：前端页面能打开但API报跨域错误

检查 `news_dashboard/.env` 中的 `CORS_ORIGINS` 是否包含你当前访问的地址（如 `http://123.45.67.89`）。

修改后重启API：
```bash
systemctl restart qknews-api
```

---

## 后续升级建议

| 需求 | 方案 |
|------|------|
| 自定义域名 | 购买域名（阿里云/腾讯云，约10-50元/年）→ 解析到ECS IP → Nginx配置server_name |
| HTTPS | 阿里云免费SSL证书 → Nginx配置443端口 |
| 自动部署 | GitHub Actions + SSH自动部署 |
| 监控告警 | 阿里云云监控（免费基础版） |
| 数据备份 | Aiven自动备份 + 定期导出SQL |

---

**有问题随时问我，部署过程中任何报错都可以贴出来。**
