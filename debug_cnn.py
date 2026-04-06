#!/usr/bin/env python3
"""
调试 CNN 和 ScienceDaily 的抓取问题
"""
import requests
from bs4 import BeautifulSoup

# 测试 CNN
print("=" * 60)
print("Testing CNN...")
url = 'https://edition.cnn.com/world'
try:
    resp = requests.get(url, timeout=20, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    print(f"Status: {resp.status_code}")
    print(f"Content length: {len(resp.text)}")
    
    # 检查是否被拦截
    if 'cloudflare' in resp.text.lower() or 'captcha' in resp.text.lower():
        print("⚠️  Detected Cloudflare/Captcha protection!")
    elif 'access denied' in resp.text.lower():
        print("⚠️  Detected Access Denied!")
    else:
        # 尝试解析链接
        soup = BeautifulSoup(resp.text, 'lxml')
        links = soup.select('.cd__headline a')
        print(f"Found {len(links)} article links with selector '.cd__headline a'")
        
        # 打印前3个链接
        for a in links[:3]:
            print(f"  - {a.get('href', 'N/A')}")
            
except Exception as e:
    print(f"Error: {e}")

# 测试 ScienceDaily
print("\n" + "=" * 60)
print("Testing ScienceDaily...")
url = 'https://www.sciencedaily.com/news/'
try:
    resp = requests.get(url, timeout=15, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    print(f"Status: {resp.status_code}")
    print(f"Content length: {len(resp.text)}")
    
    if 'cloudflare' in resp.text.lower():
        print("⚠️  Detected Cloudflare protection!")
    else:
        soup = BeautifulSoup(resp.text, 'lxml')
        import re
        links = soup.find_all('a', href=re.compile(r'/releases/\d{4}/\d{2}/'))
        print(f"Found {len(links)} article links with pattern '/releases/yyyy/mm/'")
        
        for a in links[:3]:
            print(f"  - {a.get('href', 'N/A')}: {a.get_text(strip=True)[:50]}")
            
except Exception as e:
    print(f"Error: {e}")
