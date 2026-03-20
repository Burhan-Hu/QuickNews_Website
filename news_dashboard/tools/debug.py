#!/usr/bin/env python3
"""
爬虫调试工具 - 检查实际HTML结构和爬虫工作情况

使用方法：
  python -m news_dashboard.tools.debug
  或
  cd news_dashboard && python -m tools.debug
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from bs4 import BeautifulSoup
import re

def debug_aljazeera():
    """调试Al Jazeera页面结构"""
    print("\n" + "="*60)
    print("调试 Al Jazeera")
    print("="*60)
    
    url = 'https://www.aljazeera.com/news/'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        response = requests.get(url, timeout=10, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        links = soup.find_all('a', href=re.compile(r'/news/\d{4}/\d{1,2}/\d{1,2}/'))
        print(f"\n找到 {len(links)} 个新闻链接")
        
        if links:
            article_url = links[0].get('href')
            if not article_url.startswith('http'):
                article_url = 'https://www.aljazeera.com' + article_url
            
            print(f"测试URL: {article_url}")
            
            article_resp = requests.get(article_url, timeout=10, headers=headers)
            article_resp.encoding = 'utf-8'
            article_soup = BeautifulSoup(article_resp.text, 'html.parser')
            
            print("\n✓ 标题 (h1):")
            title = article_soup.find('h1')
            if title:
                print(f"  {title.get_text(strip=True)[:60]}")
            
            print("\n✓ 发布时间 (time):")
            time_elem = article_soup.find('time')
            if time_elem:
                print(f"  {time_elem.get('datetime', time_elem.get_text(strip=True))}")
            
            print("\n✓ 正文 (article标签):")
            article_elem = article_soup.find('article')
            if article_elem:
                paragraphs = article_elem.find_all('p')
                print(f"  找到article标签，{len(paragraphs)}个<p>")
            
            print("\n✓ 图片/视频:")
            images = article_soup.find_all('img')
            videos = article_soup.find_all('iframe')
            print(f"  图片: {len(images)}, 视频: {len(videos)}")
    
    except Exception as e:
        print(f"✗ 错误: {e}")

def debug_globaltimes():
    """调试环球时报页面结构"""
    print("\n" + "="*60)
    print("调试环球时报")
    print("="*60)
    
    url = 'https://www.globaltimes.cn/world/index.html'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        response = requests.get(url, timeout=10, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        links = soup.find_all('a', href=re.compile(r'/page/\d{6}/\d+\.shtml'))
        print(f"\n找到 {len(links)} 个新闻链接")
        
        if links:
            article_url = links[0].get('href')
            if not article_url.startswith('http'):
                article_url = 'https://www.globaltimes.cn' + article_url
            
            print(f"测试URL: {article_url}")
            
            article_resp = requests.get(article_url, timeout=10, headers=headers)
            article_resp.encoding = 'utf-8'
            article_soup = BeautifulSoup(article_resp.text, 'html.parser')
            
            print("\n✓ 标题 (h1):")
            title = article_soup.find('h1')
            if title:
                print(f"  {title.get_text(strip=True)[:60]}")
            
            print("\n✓ 发布时间:")
            for selector in ['span[class*="date"]', '[class*="pubTime"]', 'time']:
                elem = article_soup.select_one(selector)
                if elem:
                    print(f"  {elem.get_text(strip=True)[:50]}")
                    break
            
            print("\n✓ 正文:")
            article_elem = article_soup.find('article')
            if article_elem:
                paragraphs = article_elem.find_all('p')
                print(f"  找到article标签，{len(paragraphs)}个<p>")
            
            print("\n✓ 图片/视频:")
            images = article_soup.find_all('img')
            videos = article_soup.find_all('iframe')
            print(f"  图片: {len(images)}, 视频: {len(videos)}")
    
    except Exception as e:
        print(f"✗ 错误: {e}")

def debug_cctv():
    """调试央视网页面结构"""
    print("\n" + "="*60)
    print("调试央视网")
    print("="*60)
    
    url = 'https://news.cctv.com/'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        response = requests.get(url, timeout=10, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        links = soup.find_all('a', href=re.compile(r'/\d{4}/\d{2}/\d{2}/'))
        print(f"\n找到 {len(links)} 个新闻链接")
        
        if links:
            article_url = links[0].get('href')
            if not article_url.startswith('http'):
                article_url = 'https://news.cctv.com' + article_url
            
            print(f"测试URL: {article_url}")
            print("➤ 如果央视网链接可访问，检查细节...（可能需要Selenium）")
    
    except Exception as e:
        print(f"✗ 错误: {e}")

if __name__ == '__main__':
    print("="*60)
    print("News Dashboard 爬虫调试工具")
    print("="*60)
    
    debug_aljazeera()
    debug_globaltimes()
    debug_cctv()
    
    print("\n" + "="*60)
    print("调试完成")
    print("="*60)
