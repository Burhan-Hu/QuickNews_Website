import time
import sys
import os
from datetime import datetime
from scheduler.jobs import NewsScheduler
from config.db_config import test_connection
import threading

def start_flask_api():
    """在后台线程启动 Flask API 服务"""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from ir.xml_api import app
    print("[Flask] 启动 API 服务于 http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, threaded=True, debug=False, use_reloader=False)

def main():
    print("=" * 60)
    print("News Dashboard Data Collector - XML检索增强版")
    print("=" * 60)
    
    # 测试数据库连接
    print("\n[Check] 测试Alwaysdata数据库连接...")
    if not test_connection():
        print("[Error] 数据库连接失败，请检查：")
        print("  1. config/db_config.py 中的host/user/password")
        print("  2. alwaysdata 是否允许你的IP访问")
        input("按Enter键退出...")
        sys.exit(1)
    
    # 测试NewsAPI配置
    from config.sources import NEWSAPI_CONFIG
    if 'your-newsapi-key' in NEWSAPI_CONFIG['api_key']:
        print("\n[Warning] NewsAPI Key未配置！RSS抓取仍可工作")
        print("  请访问 https://newsapi.org 注册获取免费API Key")
    else:
        print("\n[Check] NewsAPI配置已找到")
    
    scheduler = NewsScheduler()
    
    try:
        scheduler.start()
        
        # 启动 Flask API 后台线程
        flask_thread = threading.Thread(target=start_flask_api, daemon=True)
        flask_thread.start()
        
        """# 立即执行一次NewsAPI
        from config.sources import NEWSAPI_CONFIG
        if NEWSAPI_CONFIG['api_key'] and 'your-newsapi-key' not in NEWSAPI_CONFIG['api_key']:
            print("\n[Init] 执行首次NewsAPI抓取...")
            api_articles, status = scheduler.fetcher.fetch_newsapi()
            if api_articles:
                processed = [scheduler.processor.process_article(a) for a in api_articles]
                processed = [a for a in processed if a is not None]
                success, failed = scheduler.storage.save_articles(processed)  # 解构元组
                print(f"[Init] NewsAPI保存: 成功{success}条, 跳过{failed}条")
                scheduler.stats['api_requests_today'] += 1
                scheduler.stats['articles_fetched'] += len(api_articles)
                scheduler.stats['articles_saved'] += success
            else:
                print("[Init] NewsAPI本次未获取到数据")
        else:
            print("\n[Init] NewsAPI未配置，跳过API抓取（仅使用RSS）")"""
        
        # 立即执行一次RSS
        print("\n[Init] 执行首次RSS抓取...")
        rss_articles = scheduler.fetcher.fetch_all_rss()
        if rss_articles:
            print(f"[Init] 获取到 {len(rss_articles)} 条RSS新闻，正在处理...")
            processed = [scheduler.processor.process_article(a) for a in rss_articles]
            processed = [a for a in processed if a is not None]
            # 【修正】解构返回值元组
            success_count, failed_count = scheduler.storage.save_articles(processed)
            print(f"[Init] 成功保存 {success_count} 条新闻到数据库，跳过 {failed_count} 条")
            scheduler.stats['articles_fetched'] += len(rss_articles)
            scheduler.stats['articles_saved'] += success_count
        else:
            print("[Init] 本次未获取到新闻，将在30分钟后重试")

        # 立即执行一次HTML源抓取
        print("\n[Init] 执行HTML网站抓取...")
        html_articles = scheduler.fetcher.fetch_all_html_sources()
        if html_articles:
            processed = [scheduler.processor.process_article(a) for a in html_articles]
            processed = [a for a in processed if a is not None]
            success, failed = scheduler.storage.save_articles(processed)
            print(f"[Init] HTML源保存: 成功{success}条, 跳过{failed}条")
            scheduler.stats['articles_fetched'] += len(html_articles)
            scheduler.stats['articles_saved'] += success
        
        print("\n[Running] 系统运行中...")
        print("  - 抓取+XML索引: 每20分钟")
        print("  - 索引补充检查: 每30分钟")
        print("  - 数据清理: 每小时")
        print("  - XML检索API: http://0.0.0.0:5000/sru")
        print("按 Ctrl+C 停止\n")
        
        while True:
            time.sleep(60)
            stats = scheduler.get_stats()
            print(f"[{datetime.now().strftime('%H:%M')}] "
                  f"今日API: {stats['api_requests_today']}/100 | "
                  f"总获取: {stats['articles_fetched']} | "
                  f"总保存: {stats['articles_saved']} | "
                  f"XML索引: {stats.get('indexed', 0)}")
            
    except KeyboardInterrupt:
        print("\n[Shutdown] 正在停止调度器...")
        scheduler.stop()
        print("[Shutdown] 已安全退出")
    except Exception as e:
        print(f"\n[Error] 发生错误: {e}")
        import traceback
        traceback.print_exc()
        scheduler.stop()
        sys.exit(1)

if __name__ == '__main__':
    main()