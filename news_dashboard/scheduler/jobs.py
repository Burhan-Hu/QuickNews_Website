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
        self.processor = ContentProcessor()
        self.storage = NewsStorage()
        
        # 统计信息
        self.stats = {
            'api_requests_today': 0,
            'articles_fetched': 0,
            'articles_saved': 0
        }
    
    def job_fetch_newsapi(self):
        """NewsAPI定时任务：每20分钟执行一次"""
        print(f"[Job] 开始执行NewsAPI抓取 {datetime.now()}")
        
        articles, status = self.fetcher.fetch_newsapi()
        if not articles:
            return
        
        # 处理数据
        processed = [self.processor.process_article(a) for a in articles]
        processed = [a for a in processed if a is not None]  # 过滤空数据
        
        # 入库
        saved = self.storage.save_articles(processed)
        
        self.stats['api_requests_today'] += 1
        self.stats['articles_fetched'] += len(articles)
        self.stats['articles_saved'] += saved
        
        if status:
            next_country = status.get('next_country', 'N/A')
            next_category = status.get('next_category', 'N/A')
            remaining = status.get('remaining', '?')
            print(f"[Job] NewsAPI状态: 剩余{remaining}次，下次[{next_category}/{next_country}]")
    
    def job_fetch_rss(self):
        """RSS定时任务：每30分钟执行一次（无限制）"""
        print(f"[Job] 开始执行RSS抓取 {datetime.now()}")
        
        articles = self.fetcher.fetch_all_rss()
        if not articles:
            return
        
        processed = [self.processor.process_article(a) for a in articles]
        processed = [a for a in processed if a is not None]  # 过滤空数据
        saved = self.storage.save_articles(processed)
        
        print(f"[Job] RSS保存完成: {saved}条")
    
    def job_cleanup(self):
        """清理任务：每30分钟执行一次"""
        print(f"[Job] 开始清理过期数据 {datetime.now()}")
        self.storage.cleanup_old_news()
    
    def start(self):
        """启动调度器"""
        # NewsAPI：每864秒（14.4分钟）一次，确保每天100次
        self.scheduler.add_job(
            self.job_fetch_newsapi,
            IntervalTrigger(seconds=NEWSAPI_CONFIG['interval_seconds']),
            id='newsapi_job',
            replace_existing=True
        )
        
        # RSS：每30分钟一次
        self.scheduler.add_job(
            self.job_fetch_rss,
            IntervalTrigger(minutes=30),
            id='rss_job',
            replace_existing=True
        )
        
        # 清理：每30分钟一次
        self.scheduler.add_job(
            self.job_cleanup,
            IntervalTrigger(minutes=30),
            id='cleanup_job',
            replace_existing=True
        )
        
        self.scheduler.start()
        print("[Scheduler] 调度器已启动")
        print(f"  - NewsAPI: 每{NEWSAPI_CONFIG['interval_seconds']}秒（20分钟）")
        print(f"  - RSS: 每30分钟")
        print(f"  - Cleanup: 每30分钟")
    
    def stop(self):
        self.scheduler.shutdown()
    
    def get_stats(self):
        return self.stats

from datetime import datetime