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
    
    def _process_and_save(self, articles, source_name):
        """处理并保存文章（流式处理，防止内存累积）"""
        if not articles:
            return 0, 0
        
        print(f"[Job] {source_name}: 开始处理 {len(articles)} 条...")
        
        # 处理
        processed = []
        for a in articles:
            try:
                clean = self.processor.process_article(a)
                if clean and clean.get('term_count', 0) > 0:
                    processed.append(clean)
            except Exception as e:
                print(f"[Processor] 处理失败: {e}")
                continue
        
        # 保存
        if processed:
            print(f"[Job] {source_name}: 开始保存 {len(processed)} 条到数据库...")
            success, failed = self.storage.save_articles(processed)
            print(f"[Job] {source_name}: 完成 (保存{success}条, 跳过{failed}条)")
            return success, failed
        else:
            print(f"[Job] {source_name}: 无有效文章可保存")
        return 0, 0
    
    def job_fetch_and_save(self):
        """抓取+保存+XML索引（流式处理，防止内存累积）"""
        print(f"\n[Job] 开始抓取 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        total_fetched = 0
        total_saved = 0
        total_failed = 0
        
        # 1. NewsAPI - 类别轮询
        api_articles, status = self.fetcher.fetch_newsapi(mode='category')
        if api_articles:
            self.stats['api_requests_today'] += 1
            total_fetched += len(api_articles)
            s, f = self._process_and_save(api_articles, "NewsAPI-Category")
            total_saved += s
            total_failed += f
            del api_articles  # 释放内存
        
        # 1b. NewsAPI - 国家轮询
        api_articles_country, status2 = self.fetcher.fetch_newsapi(mode='country')
        if api_articles_country:
            self.stats['api_requests_today'] += 1
            total_fetched += len(api_articles_country)
            s, f = self._process_and_save(api_articles_country, "NewsAPI-Country")
            total_saved += s
            total_failed += f
            del api_articles_country  # 释放内存
        
        # 2. RSS源
        rss_articles = self.fetcher.fetch_all_rss()
        if rss_articles:
            total_fetched += len(rss_articles)
            s, f = self._process_and_save(rss_articles, "RSS")
            total_saved += s
            total_failed += f
            del rss_articles  # 释放内存
        
        # 3. HTML源（使用 fetch_all_html_sources 统一抓取，避免漏源）
        try:
            html_articles = self.fetcher.html_fetcher.fetch_all_html_sources()
            if html_articles:
                total_fetched += len(html_articles)
                s, f = self._process_and_save(html_articles, "HTML Sources")
                total_saved += s
                total_failed += f
                del html_articles
        except Exception as e:
            print(f"[Job] HTML源抓取失败: {e}")
        
        # 更新统计
        self.stats['articles_fetched'] += total_fetched
        self.stats['articles_saved'] += total_saved
        self.stats['failed'] += total_failed
        self.stats['indexed'] += total_saved
        
        print(f"[Job] 总计: 抓取{total_fetched}条, 保存{total_saved}条, 跳过{total_failed}条")
        
        # 【新增】爬取结束后立即更新热点话题（基于最新新闻聚类）
        if total_saved > 0:
            print("[Job] 开始更新热点话题...")
            try:
                # 导入并执行聚类（使用动态路径兼容Linux/Windows）
                import sys, os
                sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
                from ir.xml_api import update_hot_topics_internal
                topic_count = update_hot_topics_internal()
                print(f"[Job] 热点话题更新完成，共{topic_count}个话题")
            except Exception as e:
                print(f"[Job] 热点话题更新失败: {e}")
                import traceback
                traceback.print_exc()
        
        # 强制垃圾回收，缓解内存泄漏
        import gc
        gc.collect()
    
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
        # 主任务：每30分钟抓取并索引（包含热点话题聚类）
        self.scheduler.add_job(
            self.job_fetch_and_save,
            IntervalTrigger(minutes=30),
            id='fetch_job',
            replace_existing=True
        )
        
        # 【注】热点话题聚类已合并到fetch_job中，爬取结束后立即执行
        # 无需单独定时任务，确保数据一致性
        
        # 【移除】Python cleanup job，改为完全依赖MySQL Event Scheduler
        # MySQL: CREATE EVENT evt_cleanup_news ON SCHEDULE EVERY 30 MINUTE DO CALL sp_cleanup_48h();
        # 避免双重cleanup导致的锁竞争
        
        self.scheduler.start()
        print("[Scheduler] 启动成功（抓取+聚类一体化版）")
    
    def stop(self):
        self.scheduler.shutdown()
        print("[Scheduler] 已停止")
    
    def get_stats(self):
        return self.stats