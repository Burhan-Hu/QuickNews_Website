"""
新闻爬虫集成测试
测试 Al Jazeera 和 Global Times 爬虫
"""

import sys
import os

# 添加核心模块到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aljazeera_fetcher import AlJazeeraFetcher
from globaltimes_fetcher import GlobalTimesFetcher
import json


def test_aljazeera():
    """测试 Al Jazeera 爬虫"""
    print("\n" + "="*60)
    print("测试 Al Jazeera 爬虫")
    print("="*60)
    
    fetcher = AlJazeeraFetcher(delay=1.0)
    
    # 测试 URL
    test_urls = [
        'https://www.aljazeera.com/news/2026/3/19/us-f-35-aircraft-makes-emergency-landing-after-a-combat-mission-over-iran',
        'https://www.aljazeera.com/news/2026/3/19/mexican-military-says-11-killed-in-raid-targeting-sinaloa-cartel-leader',
    ]
    
    print("\n[1] 测试单篇文章爬取")
    print("-" * 60)
    for url in test_urls[:1]:  # 只测试第一个以节省时间
        article = fetcher.fetch_article(url)
        
        if 'error' not in article:
            print(f"\n✓ 成功获取文章")
            print(f"标题: {article['title'][:80]}")
            print(f"作者: {article['author']}")
            print(f"发布时间: {article['publish_date']}")
            print(f"图片数: {len(article['images'])}")
            print(f"视频数: {len(article['videos'])}")
            print(f"正文长度: {len(article['content']) if article['content'] else 0} 字符")
        else:
            print(f"\n✗ 爬取失败: {article['error']}")
    
    print("\n[2] 测试列表爬取")
    print("-" * 60)
    articles = fetcher.fetch_list(category='news')
    if articles:
        print(f"✓ 成功获取 {len(articles)} 篇新闻")
        for i, article in enumerate(articles[:3], 1):
            print(f"  {i}. {article['title'][:60]}")
            print(f"     URL: {article['url'][:60]}")
    else:
        print("✗ 未获取到新闻")


def test_globaltimes():
    """测试环球时报爬虫"""
    print("\n" + "="*60)
    print("测试环球时报 (Global Times) 爬虫")
    print("="*60)
    
    fetcher = GlobalTimesFetcher(delay=1.0)
    
    # 测试 URL
    test_urls = [
        'https://www.globaltimes.cn/page/202603/1357248.shtml',
        'https://www.globaltimes.cn/page/202603/1357239.shtml',
    ]
    
    print("\n[1] 测试单篇文章爬取")
    print("-" * 60)
    for url in test_urls[:1]:  # 只测试第一个
        article = fetcher.fetch_article(url)
        
        if 'error' not in article:
            print(f"\n✓ 成功获取文章")
            print(f"标题: {article['title'][:80]}")
            print(f"作者: {article['author']}")
            print(f"发布时间: {article['publish_date']}")
            print(f"图片数: {len(article['images'])}")
            print(f"视频数: {len(article['videos'])}")
            print(f"正文长度: {len(article['content']) if article['content'] else 0} 字符")
        else:
            print(f"\n✗ 爬取失败: {article['error']}")
    
    print("\n[2] 测试列表爬取 - 国际频道")
    print("-" * 60)
    articles = fetcher.fetch_list(channel='world')
    if articles:
        print(f"✓ 成功获取 {len(articles)} 篇新闻")
        for i, article in enumerate(articles[:3], 1):
            print(f"  {i}. {article['title'][:60]}")
            print(f"     URL: {article['url'][-30:]}")
    else:
        print("✗ 未获取到新闻")
    
    print("\n[3] 测试时间解析")
    print("-" * 60)
    test_dates = [
        "Mar 20, 2026 12:04 AM",
        "Mar 19, 2026",
    ]
    for date_str in test_dates:
        parsed = GlobalTimesFetcher.parse_datetime(date_str)
        print(f"'{date_str}' -> {parsed}")


def export_sample_data():
    """导出示例数据"""
    print("\n" + "="*60)
    print("导出示例数据")
    print("="*60)
    
    fetcher_aj = AlJazeeraFetcher(delay=1.0)
    fetcher_gt = GlobalTimesFetcher(delay=1.0)
    
    data = {
        'aljazeera': {
            'list': fetcher_aj.fetch_list('news')[:3],
            'articles': []
        },
        'globaltimes': {
            'list': fetcher_gt.fetch_list('world')[:3],
            'articles': []
        }
    }
    
    # 只爬取列表中的第一篇文章作为示例
    if data['aljazeera']['list']:
        article = fetcher_aj.fetch_article(data['aljazeera']['list'][0]['url'])
        if 'error' not in article:
            # 简化输出
            article['content'] = article['content'][:500] if article['content'] else None
            data['aljazeera']['articles'].append(article)
    
    if data['globaltimes']['list']:
        article = fetcher_gt.fetch_article(data['globaltimes']['list'][0]['url'])
        if 'error' not in article:
            article['content'] = article['content'][:500] if article['content'] else None
            data['globaltimes']['articles'].append(article)
    
    # 保存为 JSON
    output_file = os.path.join(os.path.dirname(__file__), '..', 'sample_news.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 示例数据已保存到: {output_file}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='新闻爬虫测试工具')
    parser.add_argument('--aljazeera', action='store_true', help='测试 Al Jazeera 爬虫')
    parser.add_argument('--globaltimes', action='store_true', help='测试环球时报爬虫')
    parser.add_argument('--all', action='store_true', help='测试所有爬虫')
    parser.add_argument('--export', action='store_true', help='导出示例数据')
    
    args = parser.parse_args()
    
    # 如果没有指定参数，默认测试所有
    if not (args.aljazeera or args.globaltimes or args.export):
        args.all = True
    
    try:
        if args.aljazeera or args.all:
            test_aljazeera()
        
        if args.globaltimes or args.all:
            test_globaltimes()
        
        if args.export:
            export_sample_data()
        
        print("\n" + "="*60)
        print("✓ 测试完成")
        print("="*60 + "\n")
        
    except KeyboardInterrupt:
        print("\n\n✗ 用户中断")
    except Exception as e:
        print(f"\n\n✗ 测试发生错误: {e}")
        import traceback
        traceback.print_exc()
