@echo off
chcp 65001 >nul
REM QuickNews 部署准备脚本（Windows 版）
REM 用于生成本地测试或 ClawCloud 部署所需的文件

echo ==========================================
echo QuickNews 部署准备脚本
echo ==========================================
echo.

echo [1/4] 检查 Node.js...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] Node.js 未安装，请先安装 Node.js 18+
    exit /b 1
)
for /f "tokens=*" %%a in ('node --version') do set NODE_VERSION=%%a
echo [OK] Node.js 已安装: %NODE_VERSION%

echo.
echo [2/4] 安装前端依赖...
cd app
if not exist "node_modules" (
    call npm install
) else (
    echo node_modules 已存在，跳过安装
)

echo.
echo [3/4] 构建前端...
call npm run build

if not exist "dist" (
    echo [X] 前端构建失败，dist 目录不存在
    exit /b 1
)
echo [OK] 前端构建成功
cd ..

echo.
echo [4/4] 检查配置文件...

if not exist "Dockerfile" (
    echo [X] Dockerfile 不存在
    exit /b 1
)
echo [OK] Dockerfile 存在

if not exist "news_dashboard\requirements.txt" (
    echo [X] requirements.txt 不存在
    exit /b 1
)
echo [OK] requirements.txt 存在

echo.
echo ==========================================
echo 部署准备完成！
echo ==========================================
echo.
echo 下一步操作：
echo.
echo 1. 本地测试（需要 Docker）：
echo    docker build -t quicknews:local-test .
echo    docker run -p 5000:5000 quicknews:local-test
echo.
echo 2. 部署到 ClawCloud：
echo    a. 访问 https://console.run.claw.cloud
echo    b. 使用 GitHub 登录
echo    c. 创建 App，选择 'Deploy from Dockerfile'
echo    d. 配置环境变量（数据库连接信息）
echo    e. 部署！
echo.
echo 3. 详细部署文档：
echo    查看 DEPLOY.md 获取完整指南
echo.
echo ==========================================
pause
