from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import json
from sqlalchemy import text
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
        
        # 【修正】兼容main.py的stats字段命名
        self.stats = {
            'api_requests_today': 0,  # 对应原api_requests
            'articles_fetched': 0,    # 总获取数
            'articles_saved': 0,      # 对应原saved
            'failed': 0,              # 保存失败数
            'indexed': 0              # XML索引数
        }
    
    def job_fetch_and_save(self):
        """抓取+保存+XML索引（完整流程）"""
        print(f"\n[Job] 开始抓取 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. 抓取数据
        articles = []
        
        # NewsAPI
        api_articles, status = self.fetcher.fetch_newsapi()
        if api_articles:
            articles.extend(api_articles)
            self.stats['api_requests_today'] += 1
        
        # RSS源
        rss_articles = self.fetcher.fetch_all_rss()
        if rss_articles:
            articles.extend(rss_articles)
        
        # HTML源
        html_articles = self.fetcher.fetch_all_html_sources()
        if html_articles:
            articles.extend(html_articles)
        
        print(f"[Job] 原始抓取: {len(articles)} 条")
        self.stats['articles_fetched'] += len(articles)
        
        # 2. 处理（分词+清洗）
        processed = []
        for a in articles:
            try:
                clean = self.processor.process_article(a)
                if clean and clean.get('term_count', 0) > 0:
                    processed.append(clean)
            except Exception as e:
                print(f"[Processor] 处理失败: {e}")
                continue
        
        print(f"[Job] 清洗分词后: {len(processed)} 条（含索引数据）")
        
        # 3. 存储（自动构建XML索引）
        if processed:
            success, failed = self.storage.save_articles(processed)
            self.stats['articles_saved'] += success
            self.stats['failed'] += failed
            self.stats['indexed'] += success  # 成功保存的都已建立XML索引
            print(f"[Job] 结果: 成功{success}条, 跳过{failed}条")
    
    def job_rebuild_missing_index(self):
        """补充构建漏掉的索引"""
        try:
            unindexed = self.storage.get_unindexed_news(hours=6)
            if not unindexed:
                return
            
            print(f"[IndexBuilder] 发现 {len(unindexed)} 条未索引新闻")
            
            for news_id, title, summary, lang in unindexed:
                try:
                    # 重新分词
                    if lang == 'zh':
                        title_terms = self.processor.tokenize_chinese(title)
                        content_terms = self.processor.tokenize_chinese(summary or title)
                    else:
                        title_terms = self.processor.tokenize_english(title)
                        content_terms = self.processor.tokenize_english(summary or title)
                    
                    # 调用存储过程补建索引
                    conn = self.storage.engine.connect()
                    conn.execute(
                        text("CALL sp_build_xml_index(:id, :tt, :ct, :lang)"),
                        {
                            'id': news_id,
                            'tt': json.dumps(title_terms),
                            'ct': json.dumps(content_terms),
                            'lang': lang
                        }
                    )
                    conn.commit()
                    conn.close()
                    self.stats['indexed'] += 1
                    
                except Exception as e:
                    print(f"[IndexBuilder] 补建索引失败 {news_id}: {e}")
        except Exception as e:
            print(f"[IndexBuilder] 检查失败: {e}")
    
    def start(self):
        # 主任务：每20分钟抓取并索引
        self.scheduler.add_job(
            self.job_fetch_and_save,
            IntervalTrigger(minutes=20),
            id='fetch_job',
            replace_existing=True
        )
        
        # 索引补充任务：每30分钟检查一次
        self.scheduler.add_job(
            self.job_rebuild_missing_index,
            IntervalTrigger(minutes=30),
            id='index_job',
            replace_existing=True
        )
        
        # 清理任务：每小时执行一次
        self.scheduler.add_job(
            self.storage.cleanup_old_news,
            IntervalTrigger(hours=1),
            id='cleanup_job',
            replace_existing=True
        )
        
        self.scheduler.start()
        print("[Scheduler] 启动成功（XML检索增强版）")
    
    def stop(self):
        self.scheduler.shutdown()
        print("[Scheduler] 已停止")
    
    def get_stats(self):
        return self.stats