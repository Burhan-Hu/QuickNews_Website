"""
Al Jazeera 新闻爬虫模块
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
from typing import Dict, List, Optional
import re

class AlJazeeraFetcher:
    """Al Jazeera 新闻爬虫"""
    
    BASE_URL = 'https://www.aljazeera.com'
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    # CSS 选择器配置
    SELECTORS = {
        'title': 'h1',
        'author': 'a[href*="/author/"]',
        'publish_date': 'time',
        'content': 'article',
        'images': 'article img',
        'videos': 'iframe[src*="youtube"], iframe[src*="player"]',
        'list_links': 'a[href^="/news/"], a[href^="/sports/"]',
    }
    
    def __init__(self, delay: float = 2.0):
        """
        初始化爬虫
        :param delay: 请求间隔（秒），避免被封IP
        """
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
    
    def fetch_article(self, url: str) -> Dict:
        """
        爬取单篇文章
        
        :param url: 文章 URL
        :return: 文章数据字典
        """
        try:
            time.sleep(self.delay)
            
            print(f"[Al Jazeera] 正在爬取: {url}")
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.content, 'html.parser')
            
            article = {
                'source': 'Al Jazeera',
                'url': url,
                'title': None,
                'author': None,
                'publish_date': None,
                'content': None,
                'images': [],
                'videos': [],
                'category': self._extract_category(url),
                'fetched_at': datetime.now().isoformat(),
            }
            
            # 提取标题
            title_elem = soup.select_one(self.SELECTORS['title'])
            if title_elem:
                article['title'] = title_elem.get_text(strip=True)
            
            # 提取发布时间
            time_elem = soup.select_one(self.SELECTORS['publish_date'])
            if time_elem:
                # 获取 datetime 属性或文本内容
                datetime_attr = time_elem.get('datetime')
                article['publish_date'] = datetime_attr or time_elem.get_text(strip=True)
            
            # 提取作者
            authors = []
            for author_elem in soup.select(self.SELECTORS['author']):
                author_text = author_elem.get_text(strip=True)
                if author_text and author_text not in authors:
                    authors.append(author_text)
            if authors:
                article['author'] = ' and '.join(authors)
            
            # 提取正文
            content_elem = soup.select_one(self.SELECTORS['content'])
            if content_elem:
                # 移除脚本、样式、侧栏等不必要元素
                for tag in content_elem.select('script, style, [class*="recommended"], [class*="sidebar"]'):
                    tag.decompose()
                # 获取所有段落
                paragraphs = content_elem.select('p')
                article['content'] = '\n\n'.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
            
            # 提取图片
            for img in soup.select(self.SELECTORS['images']):
                src = img.get('src', '')
                if src:
                    # 处理相对 URL
                    if src.startswith('/'):
                        src = self.BASE_URL + src
                    
                    img_data = {
                        'src': src,
                        'alt': img.get('alt', ''),
                        'title': img.get('title', '')
                    }
                    article['images'].append(img_data)
            
            # 提取视频
            for video in soup.select(self.SELECTORS['videos']):
                src = video.get('src', '')
                if src:
                    article['videos'].append({
                        'src': src,
                        'type': 'iframe'
                    })
            
            print(f"[Al Jazeera] ✓ 成功爬取: {article['title']}")
            return article
            
        except requests.RequestException as e:
            print(f"[Al Jazeera] ✗ 请求错误: {url} - {e}")
            return {'error': str(e), 'url': url}
        except Exception as e:
            print(f"[Al Jazeera] ✗ 解析错误: {url} - {e}")
            return {'error': str(e), 'url': url}
    
    def fetch_list(self, category: str = 'news', page: int = 1) -> List[Dict]:
        """
        爬取新闻列表
        
        注意: Al Jazeera 首页使用 React 动态加载，可能需要 Selenium
        
        :param category: 分类 (news, sports, features, opinions, economy)
        :param page: 页号
        :return: 新闻列表
        """
        try:
            url = f'{self.BASE_URL}/{category}/'
            print(f"[Al Jazeera] 正在爬取列表: {url}")
            
            time.sleep(self.delay)
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.content, 'html.parser')
            articles = []
            
            # 尝试多种选择器找到文章链接
            selectors = [
                'a[href^="/news/"]',
                'a[href^="/sports/"]',
                'a[href^="/features/"]',
                'a[href^="/opinions/"]',
                'h2 a',
                'h3 a',
            ]
            
            found_links = set()
            for selector in selectors:
                for link in soup.select(selector):
                    href = link.get('href', '')
                    if href and '/2026/' in href and href not in found_links:
                        text = link.get_text(strip=True)
                        if text and len(text) > 10:  # 过滤短标题
                            found_links.add(href)
                            articles.append({
                                'title': text,
                                'url': href if href.startswith('http') else self.BASE_URL + href,
                                'category': category
                            })
            
            print(f"[Al Jazeera] ✓ 找到 {len(articles)} 篇新闻")
            return articles
            
        except Exception as e:
            print(f"[Al Jazeera] ✗ 列表爬取失败: {e}")
            return []
    
    def _extract_category(self, url: str) -> str:
        """从 URL 提取分类"""
        parts = url.split('/')
        for i, part in enumerate(parts):
            if i < len(parts) - 2 and parts[i + 2].isdigit():
                return part
        return 'other'
