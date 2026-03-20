#!/usr/bin/env python3
"""
快速爬虫测试工具 - 测试各个网站的爬虫工作情况

使用方法：
  python -m news_dashboard.tools.test_sites
  python -m news_dashboard.tools.test_sites --verbose
  python -m news_dashboard.tools.test_sites --single xinhua
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from datetime import datetime

def print_header(title):
    """打印分隔符"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_section(title):
    """打印小标题"""
    print(f"\n▶ {title}")
    print("-" * 50)

def test_single_site(fetcher_class, method_name, display_name):
    """测试单个网站"""
    try:
        print_section(display_name)
        
        fetcher = fetcher_class()
        fetch_method = getattr(fetcher, method_name)
        
        start_time = time.time()
        articles = fetch_method()
        elapsed = time.time() - start_time
        
        print(f"状态: ✓ SUCCESS")
        print(f"耗时: {elapsed:.2f} 秒")
        print(f"获取文章数: {len(articles)} 条")
        
        if articles:
            article = articles[0]
            title = article.get('title', 'N/A')[:60]
            source = article.get('source_name', 'N/A')
            pub_time = article.get('published_at', 'N/A')
            content_len = len(article.get('content', ''))
            images_count = len(article.get('images', []))
            videos_count = len(article.get('videos', []))
            
            print(f"\n第一条文章:")
            print(f"  标题: {title}...")
            print(f"  来源: {source}")
            print(f"  时间: {pub_time}")
            print(f"  正文: {content_len} 字")
            print(f"  媒体: 图{images_count} 视{videos_count}")
            
            if '--verbose' in sys.argv:
                print(f"\n  完整字段:")
                for key, val in article.items():
                    if key not in ['content', 'images', 'videos']:
                        print(f"    {key}: {str(val)[:100]}")
        else:
            print(f"⚠ 注意: 未获取到任何文章")
        
        return True, len(articles)
    
    except Exception as e:
        print(f"状态: ✗ FAILED")
        print(f"错误: {str(e)}")
        
        if '--debug' in sys.argv:
            import traceback
            traceback.print_exc()
        
        return False, 0

def main():
    """主测试函数"""
    print_header("🚀 爬虫快速测试")
    
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python: {sys.version.split()[0]}")
    
    print(f"\n参数说明:")
    print(f"  --verbose  显示详细的文章字段信息")
    print(f"  --debug    显示完整的错误堆栈跟踪")
    print(f"  --single <site>  只测试单个网站")
    
    try:
        from core.html_fetcher import HTMLNewsFetcher
    except ImportError:
        try:
            from news_dashboard.core.html_fetcher import HTMLNewsFetcher
        except ImportError:
            print("\n✗ 无法导入HTMLNewsFetcher，请确保在news_dashboard目录中运行")
            sys.exit(1)
    
    # 定义要测试的网站
    sites = [
        (HTMLNewsFetcher, 'fetch_xinhua', '新华网'),
        (HTMLNewsFetcher, 'fetch_scmp', 'SCMP'),
        (HTMLNewsFetcher, 'fetch_cnn', 'CNN'),
        (HTMLNewsFetcher, 'fetch_nytimes', '纽约时报'),
        (HTMLNewsFetcher, 'fetch_cctv', '央视网'),
        (HTMLNewsFetcher, 'fetch_aljazeera', 'Al Jazeera'),
        (HTMLNewsFetcher, 'fetch_globaltimes', '环球时报'),
    ]
    
    # 检查是否指定了单个网站
    single_site = None
    if '--single' in sys.argv:
        idx = sys.argv.index('--single')
        if idx + 1 < len(sys.argv):
            single_site = sys.argv[idx + 1].lower()
    
    # 执行测试
    results = []
    total_articles = 0
    
    for fetcher_class, method_name, display_name in sites:
        # 如果指定了单个网站，只测试那个
        if single_site and single_site not in method_name.lower() and single_site not in display_name.lower():
            continue
        
        success, count = test_single_site(fetcher_class, method_name, display_name)
        results.append((display_name, success, count))
        total_articles += count
    
    # 打印总结
    print_header("📊 测试总结")
    
    success_count = sum(1 for _, s, _ in results if s)
    total_count = len(results)
    
    print(f"总网站数: {total_count}")
    print(f"成功: {success_count}")
    print(f"失败: {total_count - success_count}")
    print(f"获取文章总数: {total_articles}")
    
    print(f"\n详细结果:")
    for site_name, success, count in results:
        status = "✓" if success else "✗"
        print(f"  {status} {site_name:15} {count:3d}条")
    
    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ 用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        if '--debug' in sys.argv:
            import traceback
            traceback.print_exc()
        sys.exit(1)
