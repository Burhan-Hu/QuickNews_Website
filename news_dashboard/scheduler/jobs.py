from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from core.fetcher import NewsFetcher
from core.processor import ContentProcessor
from core.storage import NewsStorage
from config.sources import NEWSAPI_CONFIG

class NewsScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.fetcher = NewsFetcher()
        self.processor = ContentProcessor()  # 精简版
        self.storage = NewsStorage()         # 存储过程版
        
        self.stats = {
            'api_requests': 0, 
            'api_requests_today': 0,
            'saved': 0, 
            'failed': 0,
            'articles_fetched': 0,
            'articles_saved': 0
        }
    
    def job_fetch_and_save(self):
        """一键抓取+保存（所有逻辑在SQL完成）"""
        print(f"\n[Job] 开始抓取 {datetime.now()}")
        
        # 1. 获取数据（Python唯一职责）
        articles = []
        
        # 尝试NewsAPI
        api_articles, status = self.fetcher.fetch_newsapi()
        if api_articles:
            articles.extend(api_articles)
            self.stats['api_requests'] += 1
        
        # 尝试RSS
        rss_articles = self.fetcher.fetch_all_rss()
        if rss_articles:
            articles.extend(rss_articles)
        
        # 尝试HTML源（ScienceDaily、俄罗斯卫星通讯社、纽约时报-中文）
        html_articles = self.fetcher.fetch_all_html_sources()
        if html_articles:
            articles.extend(html_articles)
        
        # 2. 基础清洗（极度精简）
        processed = []
        for a in articles:
            clean = self.processor.process_article(a)
            if clean:
                processed.append(clean)
        
        print(f"[Job] 清洗后: {len(processed)} 条")
        
        # 3. 保存（全部逻辑移交SQL存储过程：校验/去重/识别/分类/索引）
        if processed:
            success, failed = self.storage.save_articles(processed)
            self.stats['saved'] += success
            self.stats['failed'] += failed
            print(f"[Job] SQL存储结果: 成功{success}条, 跳过{failed}条(长度/重复)")
    
    def start(self):
        # 每20分钟抓取一次（Alwaysdata免费版资源有限，不要过于频繁）
        self.scheduler.add_job(
            self.job_fetch_and_save,
            IntervalTrigger(minutes=20),
            id='fetch_job',
            replace_existing=True
        )
        
        # 可选：手动清理备份（如果SQL Event未启用）
        # self.scheduler.add_job(
        #     lambda: self.storage.cleanup_old_news(),
        #     IntervalTrigger(hours=1),
        #     id='cleanup_backup'
        # )
        
        self.scheduler.start()
        print("[Scheduler] 启动成功（轻量Python + 重度SQL模式）")
    
    def stop(self):
        """停止调度器"""
        self.scheduler.shutdown()
        print("[Scheduler] 调度器已停止")
    
    def get_stats(self):
        """获取统计信息"""
        return self.stats

from datetime import datetime