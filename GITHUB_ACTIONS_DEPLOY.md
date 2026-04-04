# GitHub Actions 自动部署指南

使用 GitHub Actions 自动构建 Docker 镜像并推送到 Docker Hub，无需本地安装 Docker。

---

## 📋 前置准备

1. **GitHub 账号**（已有）
2. **Docker Hub 账号**（需要注册）
3. **代码已推送到 GitHub**

---

## 步骤 1：注册 Docker Hub 账号

1. 访问 https://hub.docker.com
2. 点击 "Sign Up" 注册账号
3. 记住你的 **用户名**（后面要用）

---

## 步骤 2：创建 Docker Hub 访问令牌

GitHub Actions 需要使用访问令牌（Token）而不是密码登录 Docker Hub。

1. 登录 Docker Hub
2. 点击右上角头像 → **"Account Settings"**
3. 左侧菜单选择 **"Security"**
4. 点击 **"New Access Token"**
5. 填写描述：`GitHub Actions CI/CD`
6. 权限选择：**Read, Write, Delete**
7. 点击 **"Generate"**
8. **⚠️ 立即复制生成的令牌**（只显示一次！）

保存好这个令牌，格式类似：`dckr_pat_xxxxxxxxxxxx`

---

## 步骤 3：配置 GitHub Secrets

在 GitHub 仓库中配置 Docker Hub 的登录信息。

1. 打开你的 GitHub 仓库页面
2. 点击顶部菜单 **"Settings"**
3. 左侧菜单选择 **"Secrets and variables"** → **"Actions"**
4. 点击 **"New repository secret"** 按钮

添加以下两个 Secrets：

### Secret 1：DOCKER_USERNAME
- **Name**: `DOCKER_USERNAME`
- **Secret**: 你的 Docker Hub 用户名（例如：`yourname`）

### Secret 2：DOCKER_PASSWORD
- **Name**: `DOCKER_PASSWORD`
- **Secret**: 步骤 2 中复制的访问令牌（`dckr_pat_xxx`）

---

## 步骤 4：推送代码触发构建

### 4.1 确保 GitHub Actions 文件已提交

我已经为你创建了 `.github/workflows/docker-build.yml` 文件，你需要把它提交到 GitHub：

```bash
# 在项目根目录执行
cd d:\qknews

git add .
git commit -m "Add GitHub Actions for Docker build"
git push origin main
```

### 4.2 查看构建状态

1. 打开 GitHub 仓库页面
2. 点击顶部 **"Actions"** 标签
3. 你应该看到正在运行的 workflow："Build and Push Docker Image"
4. 点击进入可以查看详细日志

等待约 3-5 分钟，构建完成后会显示 ✅ 绿色对勾。

---

## 步骤 5：验证镜像已推送

1. 访问 https://hub.docker.com/repositories
2. 登录你的账号
3. 应该能看到名为 `quicknews` 的仓库
4. 标签应为 `latest`

---

## 步骤 6：在 ClawCloud 部署

### 6.1 获取镜像地址

构建完成后，你的镜像地址是：
```
docker.io/yourname/quicknews:latest
```

（将 `yourname` 替换为你的 Docker Hub 用户名）

### 6.2 ClawCloud 配置

回到你之前看到的 ClawCloud 部署界面，填写：

| 配置项 | 值 |
|--------|-----|
| **Application Name** | `quicknews` |
| **Image Name** | `yourname/quicknews:latest` |
| **CPU** | `0.5` |
| **Memory** | `1 GB` |
| **Container Port** | `5000` |
| **Public Access** | **ON** |

### 6.3 环境变量

添加以下环境变量：
```
DB_HOST=mysql-quicknews.alwaysdata.net
DB_PORT=3306
DB_USER=quicknews
DB_PASSWORD=hbhhbh1010110
DB_NAME=quicknews_maindb
FLASK_ENV=production
TZ=Asia/Shanghai
```

### 6.4 部署

点击 **"Deploy Application"**，等待 2-3 分钟即可完成部署。

---

## 🔄 后续更新代码

以后每次更新代码，只需要：

```bash
git add .
git commit -m "更新描述"
git push origin main
```

GitHub Actions 会自动：
1. 构建新的 Docker 镜像
2. 推送到 Docker Hub
3. 你可以在 ClawCloud 手动重启服务，或设置自动更新

---

## ❓ 常见问题

### Q1: GitHub Actions 构建失败
**检查点**：
- GitHub Secrets 是否配置正确？
- Docker Hub 访问令牌是否有 `Read, Write` 权限？
- 查看 Actions 日志中的具体错误信息

### Q2: ClawCloud 拉取镜像失败
**检查点**：
- 镜像是否为 Public？（Docker Hub 仓库设置）
- 镜像地址是否正确？
- 用户名和仓库名是否拼写正确？

### Q3: 如何触发重新构建？
**方法**：
- 推送新代码到 main 分支
- 或手动触发：GitHub → Actions → 选择 workflow → Run workflow

---

## 📊 费用说明

| 服务 | 费用 | 说明 |
|------|------|------|
| **GitHub Actions** | 免费 | 公开仓库无限使用 |
| **Docker Hub** | 免费 | 公开仓库无限存储 |
| **ClawCloud** | $5/月 | 免费额度内 |

**总计：$0**（都在免费额度内）

---

## 🎯 下一步

1. ✅ 注册 Docker Hub
2. ✅ 创建访问令牌
3. ✅ 配置 GitHub Secrets
4. ✅ 推送代码触发构建
5. ✅ 在 ClawCloud 部署

有问题随时问我！
