# ClawCloud MySQL 自建部署指南

## 概述
将数据库从 Alwaysdata 迁移到 ClawCloud 自建 MySQL，获得完整的 Event Scheduler 支持。

## 资源需求（$5/月免费额度内）

| 服务 | CPU | 内存 | 存储 | 费用 |
|------|-----|------|------|------|
| Python 应用 | 0.5 vCPU | 1 GB | 5 GB | ~$2.16/月 |
| MySQL 8.0 | 0.25 vCPU | 512 MB | 5 GB | ~$1.5/月 |
| **总计** | 0.75 vCPU | 1.5 GB | 10 GB | **~$3.66/月** |

## 部署步骤

### 1. 本地准备

```bash
# 安装依赖
pip install pymysql

# 执行数据备份
python migrate_data.py
```

### 2. ClawCloud 创建应用

1. 登录 [ClawCloud Console](https://console.run.claw.cloud)
2. 点击 "Create App"
3. 选择 **"Deploy from Dockerfile"**

### 3. 配置环境变量

在 ClawCloud 应用设置中添加：

```bash
# 数据库配置（新 MySQL）
DB_HOST=mysql
DB_PORT=3306
DB_USER=quicknews
DB_PASSWORD=QuickNews@2026
DB_NAME=quicknews_maindb

# Flask 配置
FLASK_ENV=production
TZ=Asia/Shanghai

# NewsAPI（可选）
NEWSAPI_KEY=your-api-key
```

### 4. 创建并运行 MySQL 服务

**方式A：使用 docker-compose（推荐）**

ClawCloud 支持 docker-compose，上传代码后自动识别 `docker-compose.yml`。

**方式B：单独创建 MySQL App**

如果不想用 docker-compose，可以单独创建一个 MySQL 应用：

1. 创建新 App，选择 "Container Registry"
2. 镜像：`mysql:8.0`
3. 环境变量：
   ```
   MYSQL_ROOT_PASSWORD=QuickNews@2026
   MYSQL_DATABASE=quicknews_maindb
   MYSQL_USER=quicknews
   MYSQL_PASSWORD=QuickNews@2026
   ```
4. 添加 Persistent Volume：
   - Mount Path: `/var/lib/mysql`
   - Size: 5 GB

### 5. 数据库配置（启用 Event Scheduler）

MySQL 启动后，执行以下 SQL：

```sql
-- 检查 Event Scheduler
SHOW VARIABLES LIKE 'event_scheduler';

-- 如果为 OFF，修改配置
SET GLOBAL event_scheduler = ON;

-- 创建 Event（如果不存在）
DROP EVENT IF EXISTS evt_cleanup_news;
DELIMITER //
CREATE EVENT evt_cleanup_news
ON SCHEDULE EVERY 30 MINUTE
STARTS CURRENT_TIMESTAMP
ON COMPLETION PRESERVE
ENABLE
DO
  CALL sp_cleanup_48h();
//
DELIMITER ;

-- 验证
SHOW EVENTS;
```

### 6. 导入数据

从 ClawCloud 控制台进入 MySQL 容器，执行：

```bash
# 上传备份文件到 ClawCloud
# 然后进入 MySQL 容器执行
mysql -u quicknews -p quicknews_maindb < db_backup.sql
```

或者使用 ClawCloud 的 Web Terminal。

### 7. 验证部署

```bash
# 查看日志确认连接成功
kubectl logs <pod-name>

# 应该看到：
# [DB Config] 连接: mysql:3306/quicknews_maindb
# [DB Test] MySQL Connected!
# [DB Test] Event Scheduler: ON
```

## 配置说明

### docker-compose.yml
- MySQL 使用 `event-scheduler=ON` 参数启动
- 数据持久化到 Volume，防止容器重启丢失
- 应用等待 MySQL 健康检查通过后才启动

### 网络配置
- 两个服务在同一个网络中
- 应用通过服务名 `mysql` 连接数据库
- 内网通信，延迟极低

## 数据备份策略

```bash
# 定期备份（每周）
mysqldump -h <host> -u quicknews -p quicknews_maindb > backup_$(date +%Y%m%d).sql

# 或使用 ClawCloud 的自动备份功能
```

## 故障排查

### 问题1: 应用无法连接 MySQL
```
[DB Test] 连接失败: (2003, "Can't connect to MySQL server...")
```
**解决**：
- 检查 MySQL 是否已启动（看 healthcheck）
- 检查 DB_HOST 是否为 `mysql`（服务名）
- 检查防火墙规则

### 问题2: Event Scheduler 未启用
```
[DB Test] Event Scheduler: OFF
```
**解决**：
```sql
SET GLOBAL event_scheduler = ON;
```
或在 MySQL 启动参数中添加 `--event-scheduler=ON`

### 问题3: 数据丢失（容器重启后）
**解决**：
- 确保 Volume 正确挂载到 `/var/lib/mysql`
- 检查 Volume 是否配置为 Persistent

## 监控与维护

### 查看资源使用
```bash
# 在 ClawCloud 控制台查看
# CPU、内存、磁盘使用情况
```

### 查看定时任务执行
```bash
# 进入 MySQL
SELECT * FROM information_schema.EVENTS;
SHOW EVENTS;

# 查看清理日志
SELECT * FROM mysql.event;
```

## 回滚方案

如果迁移失败，可以回滚到 Alwaysdata：

1. 修改 `db_config.py` 中的 `DB_HOST` 回 Alwaysdata 地址
2. 重新部署应用
3. 数据在 Alwaysdata 中保持不变

## 费用优化建议

1. **监控资源使用**：如果实际使用低于配置，可降低 CPU/内存
2. **设置告警**：在 $4.5 时收到通知，避免超出免费额度
3. **定期清理**：Event Scheduler 会自动清理 48 小时前的数据

## 联系方式

如有问题，请联系：
- ClawCloud 支持：https://console.run.claw.cloud/support
- 项目维护者：...
