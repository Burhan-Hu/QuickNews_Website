import time
import sys
from scheduler.jobs import NewsScheduler
from config.db_config import test_connection  # 添加导入

def main():
    print("=" * 60)
    print("News Dashboard Data Collector")
    print("=" * 60)
    
    # 首先测试数据库连接
    print("\n[Check] 测试Alwaysdata数据库连接...")
    if not test_connection():
        print("[Error] 数据库连接失败，请检查：")
        print("  1. config/db_config.py 中的host/user/password")
        print("  2. certs/ca.pem 文件是否存在")
        print("  3. alwaysdata 是否允许你的IP访问（Console -> Security -> IP Allowlist）")
        input("按Enter键退出...")
        sys.exit(1)
    
    # 测试NewsAPI配置
    from config.sources import NEWSAPI_CONFIG
    if 'your-newsapi-key' in NEWSAPI_CONFIG['api_key']:
        print("\n[Warning] NewsAPI Key未配置！RSS抓取仍可工作，但NewsAPI将跳过")
        print("  请访问 https://newsapi.org 注册获取免费API Key")
    else:
        print("\n[Check] NewsAPI配置已找到")
    
    scheduler = NewsScheduler()
    
    try:
        scheduler.start()
        
        # 立即执行一次NewsAPI（新增）
        from config.sources import NEWSAPI_CONFIG
        if NEWSAPI_CONFIG['api_key'] and 'your-newsapi-key' not in NEWSAPI_CONFIG['api_key']:
            print("\n[Init] 执行首次NewsAPI抓取...")
            api_articles, status = scheduler.fetcher.fetch_newsapi()
            if api_articles:
                processed = [scheduler.processor.process_article(a) for a in api_articles]
                processed = [a for a in processed if a is not None]  # 过滤空数据
                success, failed = scheduler.storage.save_articles(processed)
                print(f"[Init] NewsAPI保存: 成功{success}条, 跳过{failed}条")
                scheduler.stats['api_requests_today'] += 1
                scheduler.stats['articles_fetched'] += len(api_articles)
                scheduler.stats['articles_saved'] += success
            else:
                print("[Init] NewsAPI本次未获取到数据")
        else:
            print("\n[Init] NewsAPI未配置，跳过API抓取（仅使用RSS）")
        
        # 立即执行一次RSS
        print("\n[Init] 执行首次RSS抓取...")
        
        # 立即执行一次测试
        print("\n[Init] 执行首次数据抓取测试...")
        rss_articles = scheduler.fetcher.fetch_all_rss()
        if rss_articles:
            print(f"[Init] 获取到 {len(rss_articles)} 条RSS新闻，正在处理...")
            processed = [scheduler.processor.process_article(a) for a in rss_articles]
            processed = [a for a in processed if a is not None]  # 过滤空数据
            saved = scheduler.storage.save_articles(processed)
            print(f"[Init] 成功保存 {saved} 条新闻到数据库")
        else:
            print("[Init] 本次未获取到新闻，将在30分钟后重试")

        # 在首次抓取时添加HTML源（国内+国际）
        print("\n[Init] 执行HTML网站抓取...")
        html_articles = scheduler.fetcher.fetch_all_html_sources()
        if html_articles:
            processed = [scheduler.processor.process_article(a) for a in html_articles]
            processed = [a for a in processed if a is not None]  # 过滤空数据
            success, failed = scheduler.storage.save_articles(processed)
            print(f"[Init] HTML源保存: 成功{success}条, 跳过{failed}条")
        
        print("\n[Running] 系统运行中...")
        print("  - 下次RSS抓取: 30分钟后")
        print("  - 下次NewsAPI抓取: 20分钟后（如果配置了Key）")
        print("  - 数据清理: 每30分钟")
        print("按 Ctrl+C 停止\n")
        
        while True:
            time.sleep(60)
            stats = scheduler.get_stats()
            print(f"[{datetime.now().strftime('%H:%M')}] "
                  f"今日API: {stats['api_requests_today']}/100 | "
                  f"总获取: {stats['articles_fetched']} | "
                  f"总保存: {stats['articles_saved']}")
            
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

from datetime import datetime

if __name__ == '__main__':
    main()