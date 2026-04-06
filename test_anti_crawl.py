#!/usr/bin/env python3
"""
测试增强 Headers 是否能抓取 CNN 和 ScienceDaily
"""
import sys
sys.path.insert(0, 'd:\\qknews\\news_dashboard')

from core.html_fetcher import HTMLNewsFetcher

def test_cnn():
    print("=" * 60)
    print("Testing CNN with enhanced headers...")
    fetcher = HTMLNewsFetcher()
    articles = fetcher.fetch_cnn()
    print(f"\nResult: {len(articles)} articles fetched")
    if articles:
        for a in articles[:2]:
            print(f"  - {a['title'][:50]}... ({len(a['content'])} chars)")

def test_sciencedaily():
    print("\n" + "=" * 60)
    print("Testing ScienceDaily with enhanced headers...")
    fetcher = HTMLNewsFetcher()
    articles = fetcher.fetch_sciencedaily()
    print(f"\nResult: {len(articles)} articles fetched")
    if articles:
        for a in articles[:2]:
            print(f"  - {a['title'][:50]}... ({len(a['content'])} chars)")

if __name__ == '__main__':
    test_cnn()
    test_sciencedaily()
