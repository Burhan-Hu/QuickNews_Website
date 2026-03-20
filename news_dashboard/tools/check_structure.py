#!/usr/bin/env python3
"""
网站HTML结构检查工具 - 快速检查网站的选择器和链接结构

使用方法：
  python -m news_dashboard.tools.check_structure
  或
  cd news_dashboard && python -m tools.check_structure
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from bs4 import BeautifulSoup

# 待检查的网站
SITES = [
    ('https://www.scmp.com/news/china', 'SCMP - China'),
    ('https://edition.cnn.com/world', 'CNN - World'),
    ('https://www.aljazeera.com/news/', 'Al Jazeera - News'),
    ('https://www.globaltimes.cn/world/index.html', 'Global Times - World'),
]

def check_site(url, name):
    """检查单个网站的结构"""
    print(f"\n{'='*60}")
    print(f"检查: {name}")
    print(f"URL: {url}")
    print('='*60)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'lxml')
        
        print(f"\n✓ HTTP {response.status_code} - 页面加载成功")
        print(f"  页面大小: {len(response.text)} 字节")
        print(f"  标题 (title): {soup.title.string[:80] if soup.title else 'N/A'}")
        
        # 检查常见容器
        print(f"\n容器选择器检查:")
        containers = [
            'article', 'div.article', 'div.card-headline', 'div.l-container',
            'section[role=main]', 'div.row', 'ul', 'div.listing',
            'div.main', 'div.container', '[class*="content"]', '[class*="article"]'
        ]
        
        for selector in containers:
            elements = soup.select(selector)
            if elements:
                count = len(elements)
                print(f"  ✓ {selector:30} 找到 {count} 个")
        
        # 检查链接
        print(f"\n链接检查:")
        links = soup.find_all('a', href=True)
        total_links = len(links)
        
        # 分类统计
        news_keywords = ['/2026/', '/news/', '/article/', '/2025/', '/2024/']
        news_links = []
        for link in links:
            href = link.get('href', '')
            if any(keyword in href for keyword in news_keywords):
                if href not in news_links:
                    news_links.append(href)
        
        print(f"  总链接数: {total_links}")
        print(f"  新闻链接: {len(news_links)}")
        print(f"\n  样本新闻链接 (前5个):")
        for link in news_links[:5]:
            print(f"    - {link[:80]}")
        
    except requests.RequestException as e:
        print(f"\n✗ 请求失败: {e}")
    except Exception as e:
        print(f"\n✗ 解析错误: {e}")

if __name__ == '__main__':
    print("\n" + "="*60)
    print("News Dashboard 网站结构检查工具")
    print("="*60)
    
    for url, name in SITES:
        try:
            check_site(url, name)
        except Exception as e:
            print(f"\n✗ {name} 检查失败: {e}")
    
    print("\n" + "="*60)
    print("检查完成")
    print("="*60)
