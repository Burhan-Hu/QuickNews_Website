"""
环球时报 (Global Times) 新闻爬虫模块
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
from typing import Dict, List, Optional
import re

class GlobalTimesFetcher:
    """环球时报新闻爬虫"""
    
    BASE_URL = 'https://www.globaltimes.cn'
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    # CSS 选择器配置
    SELECTORS = {
        'title': 'h1',
        'author': 'a[href*="/author/"]',
        'publish_date': '[class*="date"], span',
        'content': 'article',
        'images': 'article img, img[src*="/Portals/"]',
        'videos': 'iframe[src*="youtube"], iframe[src*="youku"], [class*="video"]',
        'list_links': 'a[href*="/page/"]',
    }
    
    # 频道 URL
    CHANNELS = {
        'world': f'{BASE_URL}/world/index.html',
        'china': f'{BASE_URL}/china/index.html',
        'home': f'{BASE_URL}/index.html',
        'opinion': f'{BASE_URL}/opinion/index.html',
        'in-depth': f'{BASE_URL}/In-depth/index.html',
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
            
            print(f"[Global Times] 正在爬取: {url}")
            resp = self.session.get(url, timeout=10)
            resp.encoding = 'utf-8'  # 环球时报使用 UTF-8
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.content, 'html.parser')
            
            article = {
                'source': 'Global Times',
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
            
            # 提取发布时间和作者
            # 格式: "Published: Mar 20, 2026 12:04 AM"
            for elem in soup.select(self.SELECTORS['publish_date']):
                text = elem.get_text(strip=True)
                
                # 查找发布时间
                if 'Published:' in text:
                    match = re.search(r'Published:\s*(.+?)(?:\n|$)', text)
                    if match:
                        article['publish_date'] = match.group(1).strip()
                
                # 查找作者 (通常含有 "By")
                if 'By ' in text:
                    match = re.search(r'By\s+(.+?)(?:\n|Published|$)', text)
                    if match:
                        article['author'] = match.group(1).strip()
            
            # 如果通过上面的方式没有获取到作者，尝试直接选择
            if not article['author']:
                author_elems = soup.select(self.SELECTORS['author'])
                if author_elems:
                    authors = [elem.get_text(strip=True) for elem in author_elems if elem.get_text(strip=True)]
                    if authors:
                        article['author'] = ' and '.join(authors)
            
            # 提取正文
            content_elem = soup.select_one(self.SELECTORS['content'])
            if not content_elem:
                # 备选选择器
                content_elem = soup.select_one('[class*="article-content"]') or soup.select_one('[class*="story-body"]')
            
            if content_elem:
                # 移除脚本、样式、侧栏等不必要元素
                for tag in content_elem.select('script, style, [class*="recommended"], [class*="sidebar"], [class*="comment"]'):
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
                    
                    # 忽略logo、icon等
                    if any(x in src for x in ['logo', 'icon', 'gray_play']):
                        continue
                    
                    img_data = {
                        'src': src,
                        'alt': img.get('alt', ''),
                        'title': img.get('title', '')
                    }
                    article['images'].append(img_data)
            
            # 提取视频
            for video in soup.select(self.SELECTORS['videos']):
                src = video.get('src', '') if video.name == 'iframe' else video.get('src', '')
                if src and 'youtube' in src or 'youku' in src or 'video' in src:
                    article['videos'].append({
                        'src': src,
                        'type': 'iframe' if video.name == 'iframe' else 'video'
                    })
            
            print(f"[Global Times] ✓ 成功爬取: {article['title']}")
            return article
            
        except requests.RequestException as e:
            print(f"[Global Times] ✗ 请求错误: {url} - {e}")
            return {'error': str(e), 'url': url}
        except Exception as e:
            print(f"[Global Times] ✗ 解析错误: {url} - {e}")
            return {'error': str(e), 'url': url}
    
    def fetch_list(self, channel: str = 'world') -> List[Dict]:
        """
        爬取新闻列表（适用于国际频道或其他频道）
        
        :param channel: 频道名称 (world, china, home, opinion, in-depth)
        :return: 新闻列表
        """
        try:
            url = self.CHANNELS.get(channel)
            if not url:
                print(f"[Global Times] ✗ 未知频道: {channel}")
                return []
            
            print(f"[Global Times] 正在爬取列表: {channel} - {url}")
            
            time.sleep(self.delay)
            resp = self.session.get(url, timeout=10)
            resp.encoding = 'utf-8'
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.content, 'html.parser')
            articles = []
            found_links = set()
            
            # 查找所有新闻链接
            for link in soup.select(self.SELECTORS['list_links']):
                href = link.get('href', '')
                
                # 过滤有效的文章链接 (/page/202603/1357248.shtml)
                if href and '/page/' in href and href not in found_links:
                    # 补全 URL
                    if not href.startswith('http'):
                        href = self.BASE_URL + href
                    
                    text = link.get_text(strip=True)
                    if text and len(text) > 10:  # 过滤短标题
                        found_links.add(href)
                        articles.append({
                            'title': text,
                            'url': href,
                            'channel': channel
                        })
            
            print(f"[Global Times] ✓ 找到 {len(articles)} 篇新闻")
            return articles
            
        except Exception as e:
            print(f"[Global Times] ✗ 列表爬取失败: {e}")
            return []
    
    def fetch_highlights(self) -> List[Dict]:
        """
        爬取首页推荐新闻
        
        :return: 热点新闻列表
        """
        return self.fetch_list('home')
    
    def _extract_category(self, url: str) -> str:
        """从 URL 提取分类"""
        # /page/202603/1357248.shtml
        if '/page/' in url:
            return 'article'
        
        # 从频道判断
        if '/world/' in url:
            return 'world'
        elif '/china/' in url:
            return 'china'
        elif '/opinion/' in url:
            return 'opinion'
        elif '/In-depth/' in url:
            return 'in-depth'
        
        return 'other'
    
    @staticmethod
    def parse_datetime(date_str: str) -> Optional[datetime]:
        """
        解析环球时报的时间格式
        格式: "Mar 20, 2026 12:04 AM"
        
        :param date_str: 时间字符串
        :return: datetime 对象
        """
        try:
            return datetime.strptime(date_str, '%b %d, %Y %I:%M %p')
        except ValueError:
            try:
                return datetime.strptime(date_str, '%b %d, %Y')
            except ValueError:
                return None
