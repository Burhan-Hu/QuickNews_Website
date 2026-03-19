-- ==========================================
-- TiDB Cloud Serverless 验证脚本（修正版）
-- 兼容 TiDB 语法，去除 MySQL 特有变量
-- ==========================================

-- 1. 基础信息（确认是 TiDB 而非本地 MySQL）
SELECT
    VERSION() as tidb_version,
    DATABASE() as current_db,
    @@port as connection_port,
    @@time_zone as server_timezone,
    NOW() as server_time;

-- 2. 创建测试库（如果不存在）
CREATE DATABASE IF NOT EXISTS test_verify;
USE test_verify;

-- 3. 创建基础表（验证 DDL）
CREATE TABLE IF NOT EXISTS test_basic (
    id INT AUTO_INCREMENT PRIMARY KEY,
    content VARCHAR(100),
    num INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. 插入测试（验证 DML + 中文）
INSERT INTO test_basic (content, num) VALUES
    ('连接成功', 1),
    ('中文测试', 2),
    ('TiDB Cloud Ready', 3);

-- 5. 查询验证
SELECT * FROM test_basic;

-- 6. 验证 Event Scheduler（项目核心！必须显示 ON）
SHOW VARIABLES LIKE 'event_scheduler';

-- 7. 验证事务支持
START TRANSACTION;
UPDATE test_basic SET num = 999 WHERE id = 1;
ROLLBACK;
SELECT * FROM test_basic WHERE id = 1;  -- 应该看到 1 而非 999

-- 8. 验证索引与查询优化器（为后续项目验证）
CREATE INDEX idx_test ON test_basic(created_at);
EXPLAIN SELECT * FROM test_basic WHERE created_at > DATE_SUB(NOW(), INTERVAL 1 HOUR);

-- 9. 验证聚合与分组（地图统计需要）
SELECT content, COUNT(*) as cnt, MAX(created_at) as latest
FROM test_basic
GROUP BY content;

-- 10. 清理测试数据
DROP TABLE test_basic;
DROP DATABASE test_verify;

SELECT 'TiDB Cloud 验证全部通过！可以开始 Schema 初始化' AS status;