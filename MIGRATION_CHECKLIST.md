# ClawCloud MySQL 迁移检查清单

## 修改的文件

### 1. 核心配置文件
- ✅ `docker-compose.yml` - 新增，定义 MySQL 和应用服务
- ✅ `Dockerfile` - 修改，添加 mysql-client 和启动脚本
- ✅ `news_dashboard/config/db_config.py` - 修改，支持环境变量
- ✅ `start.sh` - 新增，智能启动脚本

### 2. 迁移工具
- ✅ `migrate_data.py` - 新增，数据迁移脚本
- ✅ `.env.example` - 新增，环境变量模板

### 3. 文档
- ✅ `DEPLOY_CLAWCLOUD_MYSQL.md` - 部署指南
- ✅ `MIGRATION_CHECKLIST.md` - 本文件

## 迁移步骤

### 阶段1：本地准备（当前阶段）

```bash
# 1. 提交代码
git add .
git commit -m "feat: 支持 ClawCloud 自建 MySQL"
git push

# 2. 备份 Alwaysdata 数据
python migrate_data.py
```

### 阶段2：ClawCloud 部署

1. **创建 MySQL 应用**
   - 登录 ClawCloud
   - 创建新 App
   - 选择 "Deploy from Dockerfile"
   - 或使用 docker-compose

2. **配置环境变量**
   - 参考 `.env.example`
   - 设置 DB_HOST=mysql

3. **添加 Persistent Volume**
   - Mount Path: `/var/lib/mysql`
   - Size: 5 GB

4. **等待 MySQL 启动**
   - 查看日志确认 MySQL 就绪
   - 确认 Event Scheduler 为 ON

### 阶段3：数据迁移

```bash
# 在 ClawCloud 控制台执行
# 上传 db_backup.sql 文件
# 进入 MySQL 容器
mysql -u quicknews -p quicknews_maindb < db_backup.sql
```

### 阶段4：验证

```bash
# 检查 Event Scheduler
mysql -e "SELECT @@event_scheduler;"

# 检查事件
mysql -e "SHOW EVENTS;"

# 检查数据
mysql -e "SELECT COUNT(*) FROM news;"
```

## 回滚计划

如果迁移失败：

1. 修改 `news_dashboard/config/db_config.py`
2. 将 `DB_HOST` 改回 Alwaysdata 地址
3. 重新部署
4. 数据在 Alwaysdata 中保持不变

## 费用监控

- 每月费用预算：$3.66 / $5
- 建议设置告警阈值：$4.5

## 验证 Event Scheduler 工作

```sql
-- 手动触发清理测试
CALL sp_cleanup_48h();

-- 检查 Event 状态
SELECT EVENT_NAME, STATUS, LAST_EXECUTED 
FROM information_schema.EVENTS;
```

## 完成标志

- [ ] MySQL 在 ClawCloud 运行
- [ ] Event Scheduler = ON
- [ ] 数据完整迁移
- [ ] 应用正常连接
- [ ] 定时清理任务正常工作
- [ ] 费用在 $5/月内
