-- 检查 Event Scheduler 状态
SELECT @@event_scheduler AS event_scheduler_status;

-- 检查已有的事件
SHOW EVENTS;

-- 如果 Event Scheduler 是 OFF，尝试开启（可能需要参数组权限）
-- SET GLOBAL event_scheduler = ON;

-- 手动测试清理存储过程
-- CALL sp_cleanup_48h();
