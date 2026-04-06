#!/usr/bin/env python3
"""
本地测试 CNN 和 ScienceDaily 抓取
"""
import sys
sys.path.insert(0, 'd:\\qknews\\news_dashboard')

from core.html_fetcher import HTMLNewsFetcher
import time

def test_cnn():
    print("=" * 60)
    print("[TEST] CNN World News")
    print("-" * 60)
    
    fetcher = HTMLNewsFetcher()
    start = time.time()
    
    try:
        articles = fetcher.fetch_cnn()
        elapsed = time.time() - start
        
        print(f"\n[RESULT] CNN: {len(articles)} articles in {elapsed:.1f}s")
        if articles:
            print("\nTop 3 articles:")
            for i, a in enumerate(articles[:3], 1):
                print(f"  {i}. {a['title'][:50]}... ({len(a['content'])} chars)")
        return len(articles)
    except Exception as e:
        print(f"[ERROR] CNN: {e}")
        return 0

def test_sciencedaily():
    print("\n" + "=" * 60)
    print("[TEST] ScienceDaily")
    print("-" * 60)
    
    fetcher = HTMLNewsFetcher()
    start = time.time()
    
    try:
        # 设置较短的超时避免等待太久
        import requests
        # 先只测试列表页
        url = 'https://www.sciencedaily.com/news/'
        session = requests.Session()
        session.headers.update(fetcher.ANTI_CRAWL_HEADERS)
        
        print(f"[TEST] Fetching {url}...")
        resp = session.get(url, timeout=15)
        print(f"[TEST] Status: {resp.status_code}, Length: {len(resp.text)}")
        
        from bs4 import BeautifulSoup
        import re
        soup = BeautifulSoup(resp.text, 'lxml')
        
        # 查找文章链接
        links = soup.find_all('a', href=re.compile(r'/releases/\d{4}/\d{2}/'))
        print(f"[TEST] Found {len(links)} article links")
        
        if links:
            # 只测试第一条
            first = links[0]
            title = first.get_text(strip=True)
            href = first.get('href', '')
            print(f"[TEST] First article: {title[:50]}...")
            print(f"[TEST] URL: {href}")
            
        elapsed = time.time() - start
        print(f"\n[RESULT] ScienceDaily: {len(links)} links found in {elapsed:.1f}s")
        return len(links)
        
    except Exception as e:
        print(f"[ERROR] ScienceDaily: {e}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == '__main__':
    print("Starting local test...")
    print(f"Python: {sys.version}")
    
    cnn_count = test_cnn()
    sd_count = test_sciencedaily()
    
    print("\n" + "=" * 60)
    print("[SUMMARY]")
    print(f"  CNN:          {cnn_count} articles")
    print(f"  ScienceDaily: {sd_count} links")
    print("=" * 60)
