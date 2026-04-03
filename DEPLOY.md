# QuickNews ClawCloud 部署指南

## 📋 部署前准备

### 1. 确认 GitHub 账号资格
- GitHub 账号注册时间 **≥ 180 天**（约 6 个月）
- 访问 https://console.run.claw.cloud 用 GitHub 登录
- 在右上角头像 → Plan 中确认看到 **"Monthly Gift Credits: $5"**

### 2. 确认数据库已就绪
- Alwaysdata 数据库已创建并可访问
- 数据库名称：`quicknews_maindb`
- 记住数据库连接信息（用户名、密码、主机地址）

### 3. 本地环境检查
```bash
# 确认已安装 Docker
docker --version

# 确认已安装 Node.js (用于本地测试构建)
node --version  # 需要 v18+

# 确认已安装 Python (用于本地测试)
python --version  # 需要 3.11+
```

---

## 🏗️ 步骤 1：本地测试构建

### 1.1 克隆/准备代码
```bash
# 确保你在项目根目录
cd /path/to/qknews

# 检查项目结构
ls -la
# 应该看到：app/, news_dashboard/, Dockerfile, DEPLOY.md
```

### 1.2 测试前端构建
```bash
cd app

# 安装依赖
npm install

# 构建生产版本
npm run build

# 确认 dist 目录已生成
ls dist/
# 应该看到：index.html, assets/
```

### 1.3 测试 Docker 构建（可选但推荐）
```bash
# 在项目根目录
cd /path/to/qknews

# 构建 Docker 镜像
docker build -t quicknews:test .

# 测试运行（需要设置环境变量）
docker run -p 5000:5000 \
  -e DB_HOST=your-alwaysdata-host \
  -e DB_USER=your-username \
  -e DB_PASSWORD=your-password \
  -e DB_NAME=quicknews_maindb \
  quicknews:test

# 访问 http://localhost:5000/health 测试
```

---

## 🚀 步骤 2：ClawCloud 部署

### 2.1 登录 ClawCloud
1. 访问 https://console.run.claw.cloud
2. 点击 **"Get Started For Free"**
3. 选择 **GitHub** 登录
4. 授权后进入控制台

### 2.2 创建应用
1. 点击左侧菜单 **"App Launchpad"**
2. 点击右上角 **"Create App"**
3. 选择 **"Deploy from Dockerfile"**

### 2.3 配置应用信息

#### 基本信息
| 配置项 | 建议值 | 说明 |
|--------|--------|------|
| **App Name** | `quicknews` | 你的应用名称（小写，无空格） |
| **Region** | `Singapore` | 推荐新加坡，延迟较低 |
| **Instance Type** | `Standard` | 免费额度支持 |

#### 资源配置（免费额度内）
| 配置项 | 建议值 | 说明 |
|--------|--------|------|
| **CPU** | `0.5 vCPU` | 节省额度，够用 |
| **Memory** | `1 GB` | 节省额度，够用 |
| **Disk** | `5 GB` | 默认即可 |

> 💡 **费用估算**：0.5 vCPU + 1GB RAM 连续运行一个月约 $2.16，在 $5 免费额度内。

### 2.4 配置环境变量
在 **"Environment Variables"** 部分添加：

```bash
# 数据库配置（使用 Alwaysdata 数据库）
DB_HOST=your-username.alwaysdata.net
DB_PORT=3306
DB_USER=your-username
DB_PASSWORD=your-password
DB_NAME=your-username_quicknews

# Flask 配置
FLASK_ENV=production

# NewsAPI 配置（可选，用于新闻抓取）
NEWSAPI_KEY=your-newsapi-key

# 时区
TZ=Asia/Shanghai
```

### 2.5 上传代码

#### 方式一：Git 仓库（推荐）
1. 将代码推送到 GitHub/GitLab
2. 在 ClawCloud 选择 **"Deploy from Git"**
3. 授权并选择仓库
4. 设置分支为 `main` 或 `master`

#### 方式二：ZIP 上传
1. 在本地打包代码（**不要包含 node_modules 和 .git**）
```bash
# 在项目根目录
zip -r quicknews-deploy.zip . \
  -x "*.git*" \
  -x "*node_modules*" \
  -x "*.pyc" \
  -x "__pycache__/*"
```
2. 在 ClawCloud 选择 **"Upload ZIP"**
3. 上传 `quicknews-deploy.zip`

### 2.6 Dockerfile 路径确认
- **Dockerfile Path**: `/Dockerfile`（根目录）
- **Port**: `5000`

### 2.7 部署应用
1. 点击 **"Deploy Application"**
2. 等待构建（约 3-5 分钟）
3. 状态变为 **"Running"** 后即可访问

---

## 🔍 步骤 3：部署后验证

### 3.1 获取公网地址
1. 在 ClawCloud 控制台点击你的应用
2. 查看 **"External URL"**
3. 地址格式：`https://quicknews-xxx.sgp1.clawcloudrun.com`

### 3.2 功能验证清单

#### ✅ 基础访问
- [ ] 访问首页，看到地球和 UI
- [ ] 开场动画正常播放（首次访问）
- [ ] 点击导航按钮，页面切换流畅

#### ✅ API 测试
```bash
# 健康检查
curl https://your-app-url.sgp1.clawcloudrun.com/health

# 预期返回：{"status": "ok", "database": "connected"}

# 获取分类
curl https://your-app-url.sgp1.clawcloudrun.com/api/categories

# 获取国家统计
curl https://your-app-url.sgp1.clawcloudrun.com/api/stats/countries

# 获取热点话题
curl https://your-app-url.sgp1.clawcloudrun.com/api/stats/topics

# XML 搜索测试
curl "https://your-app-url.sgp1.clawcloudrun.com/sru?query=*&maximumRecords=10"
```

#### ✅ 页面功能
- [ ] 搜索页：分类按钮正常显示
- [ ] 搜索页：点击分类加载对应新闻
- [ ] 搜索页：搜索功能正常工作
- [ ] 可视化页：热力图显示正常
- [ ] 可视化页：点击国家加载新闻
- [ ] 可视化页：热点话题显示合理（非停用词）

---

## ⚙️ 步骤 4：配置优化

### 4.1 调整抓取频率（节省流量）
在 `news_dashboard/scheduler/jobs.py` 中修改：
```python
SCHEDULE_CONFIG = {
    'rss_interval': 30,      # RSS：30分钟
    'html_interval': 60,     # HTML：1小时
    'api_interval': 120,     # NewsAPI：2小时
}
```

修改后重新部署。

### 4.2 自定义域名（可选）
1. 在 ClawCloud 应用设置中找到 **"Custom Domain"**
2. 添加你的域名（如 `news.yourdomain.com`）
3. 在 DNS 服务商添加 CNAME 记录：
   - 主机记录：`news`
   - 记录值：`quicknews-xxx.sgp1.clawcloudrun.com`
4. 等待 DNS 生效（通常 5-30 分钟）

### 4.3 启用 HTTPS
- ClawCloud 自动为默认域名提供 HTTPS
- 自定义域名需在设置中开启 **"Auto HTTPS"**

---

## 📊 监控与维护

### 5.1 查看日志
1. 在 ClawCloud 控制台点击应用
2. 进入 **"Logs"** 标签
3. 可查看实时日志和历史日志

### 5.2 监控资源使用
1. 进入 **"Metrics"** 标签
2. 查看 CPU、内存、流量使用情况
3. 确保在 $5 额度内

### 5.3 手动重启
- 在控制台点击 **"Restart"** 按钮
- 或推送新代码自动触发重新部署

---

## 🐛 常见问题

### Q1: 部署失败，提示 "Build Failed"
**解决方案**：
1. 检查 Dockerfile 是否在根目录
2. 检查 `requirements.txt` 是否包含所有依赖
3. 查看构建日志，安装缺失的系统依赖

### Q2: 访问首页显示 "Not Found"
**解决方案**：
1. 确认前端已正确构建（`app/dist/` 目录存在）
2. 检查 Dockerfile 中是否复制了静态文件
3. 检查 Flask 路由是否正确配置

### Q3: 数据库连接失败
**解决方案**：
1. 检查环境变量 `DB_HOST`, `DB_USER`, `DB_PASSWORD` 是否正确
2. 确认 Alwaysdata 允许 ClawCloud IP 访问
3. 在 ClawCloud 容器内测试连接：
   ```bash
   python -c "from config.db_config import test_connection; print(test_connection())"
   ```

### Q4: 流量超出 10GB
**解决方案**：
1. 降低抓取频率（见 4.1）
2. 使用 Cloudflare CDN 缓存静态资源
3. 考虑升级到 Hobby 套餐（$5/月，无限流量）

### Q5: 抓取任务不执行
**解决方案**：
1. 检查 `main.py` 是否在容器内正确运行
2. 查看日志确认 scheduler 已启动
3. 手动触发一次抓取测试：
   ```bash
   python -c "from scheduler.jobs import NewsScheduler; s = NewsScheduler(); s.run_job('rss')"
   ```

---

## 📝 部署清单（Checklist）

部署前：
- [ ] GitHub 账号 ≥ 180 天
- [ ] Alwaysdata 数据库可访问
- [ ] 本地 Docker 构建测试通过

部署中：
- [ ] 资源配置：0.5 vCPU + 1GB RAM
- [ ] 环境变量配置正确
- [ ] Dockerfile 路径正确
- [ ] 端口设置为 5000

部署后：
- [ ] 健康检查 API 正常
- [ ] 首页正常显示
- [ ] 搜索功能正常
- [ ] 可视化页面正常
- [ ] 抓取任务正常运行

---

## 🔗 相关链接

- ClawCloud 控制台：https://console.run.claw.cloud
- Alwaysdata 数据库：https://www.alwaysdata.com
- 项目仓库：https://github.com/yourusername/qknews
- NewsAPI 获取 Key：https://newsapi.org

---

**部署完成！享受你的 QuickNews 新闻可视化平台吧！🎉**
