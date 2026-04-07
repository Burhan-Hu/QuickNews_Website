-- 迁移脚本：更新新闻来源配置
-- 运行此脚本前请备份数据库
-- 用途：移除 CNN/ScienceDaily，添加 iDaily/RFI-中文

-- 1. 首先查看当前来源
SELECT source_id, source_name, source_type FROM sources ORDER BY source_id;

-- 2. 删除旧的来源（CNN 和 ScienceDaily）
-- 注意：如果有外键约束，可能需要先删除相关新闻或更新 source_id
DELETE FROM sources WHERE source_name IN ('CNN', 'ScienceDaily');

-- 3. 删除其他不再使用的 RSS 来源（如果有）
DELETE FROM sources WHERE source_name IN (
    '36氪', '虎嗅网', 'RT-中文', 'FoxNews-World', '南华早报-SCMP', 
    'FoxNews-Politics', 'ChinaDaily', 'NewYorker', '凤凰网-军事', 
    'AP-美联社', '经济日报'
);

-- 4. 添加新的 RSS 来源
INSERT INTO sources (source_name, source_url, source_type, language, reliability_score) VALUES
('iDaily', 'https://plink.anyfeeder.com/idaily/today', 'rss', 'zh', 7),
('RFI-中文', 'https://plink.anyfeeder.com/rfi/cn', 'rss', 'zh', 8);

-- 5. 更新 HTML 来源的 source_id（按照新的映射）
-- 注意：如果已有数据，需要谨慎处理，可能需要更新 news 表中的 source_id

-- 6. 查看更新后的来源
SELECT source_id, source_name, source_type, source_url FROM sources ORDER BY source_id;
