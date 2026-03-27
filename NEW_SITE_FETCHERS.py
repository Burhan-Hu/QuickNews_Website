# 新增网站爬取方法（添加到 html_fetcher.py 的 HTMLNewsFetcher 类中）

"""
= 使用说明 =
这些方法应该被添加到 html_fetcher.py 的 HTMLNewsFetcher 类中。
同时需要在 fetch_all_domestic() 或其他调用点合并结果。

= URL 模式总结 =

纽约时报: https://cn.nytimes.com/[category]/YYYYMMDD/slug/zh-hant/
央视网文字: https://news.cctv.com/YYYY/MM/DD/ARTIXXX.shtml
央视网视频: https://v.cctv.com/YYYY/MM/DD/VIDEXXX.shtml
观察者网: https://www.guancha.cn/[category]/YYYY_MM_DD_xxx.html
华盛顿邮报: https://www.washingtonpost.com/[section]/YYYY/MM/DD/xxxxx/
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil import parser as date_parser
import time
import re

class HTMLNewsFetcherExtension:
    """
    为 HTMLNewsFetcher 类的扩展方法
    所有这些方法都应该有相同的签名：
    def fetch_xxxx(self) -> list of articles
    """
    
    def fetch_nytimes(self):
        """
        纽约时报中文版爬取
        URL: https://cn.nytimes.com/
        支持频道：china (中国), world (国际), business (商业), opinion (评论)
        """
        articles = []
        channels = ['china', 'world', 'business']  # 添加额外频道可扩展
        
        try:
            for channel in channels:
                url = f'https://cn.nytimes.com/{channel}/'
                print(f"[HTML] 抓取: 纽约时报中文版-{channel}")
                
                try:
                    response = self.session.get(url, timeout=15)
                    response.encoding = 'utf-8'
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 纽约时报的新闻列表通常在文章链接中
                    # 查找所有指向文章的链接
                    article_links = soup.find_all('a', href=re.compile(r'/[a-z-]+/\d{8}/'))
                    
                    if not article_links:
                        # 备选选择器
                        article_links = soup.select('div[class*="article"] a')
                    
                    processed_urls = set()
                    
                    for link in article_links[:15]:  # 每个频道取前15条
                        try:
                            href = link.get('href', '').strip()
                            title = link.get_text(strip=True)
                            
                            if not href or not title:
                                continue
                            
                            # 确保是完整URL
                            if not href.startswith('http'):
                                if href.startswith('/'):
                                    href = 'https://cn.nytimes.com' + href
                                elif not href.startswith('https'):
                                    continue
                            
                            # 去重
                            if href in processed_urls:
                                continue
                            processed_urls.add(href)
                            
                            # 只处理文章链接（包含日期）
                            if not re.search(r'/\d{8}/', href):
                                continue
                            
                            # 获取详情页内容
                            print(f"  [Debug] 获取: {title[:30]}...")
                            content, pub_time, images, videos = self._fetch_nytimes_article(href)
                            
                            if content:
                                articles.append({
                                    'title': title[:300],
                                    'summary': content[:500],
                                    'content': content[:15000],
                                    'source_url': href,
                                    'source_name': '纽约时报中文版',
                                    'published_at': pub_time,
                                    'image_url': images[0]['url'] if images else None,
                                    'images': images,
                                    'videos': videos,
                                    'category_hint': channel,
                                    'country_hint': 'HK',  # 繁体中文版
                                    'fetch_method': 'html_nytimes'
                                })
                                print(f"  [Debug] ✓ 成功: {title[:20]}... ({len(content)}字)")
                            else:
                                print(f"  [Debug] ✗ 内容获取失败")
                            
                            # 礼貌爬取
                            time.sleep(1.5)
                        
                        except Exception as e:
                            print(f"  [Debug] 解析单条失败: {e}")
                            continue
                
                except Exception as e:
                    print(f"[HTML] ✗ 纽约时报-{channel}: {e}")
                    continue
                
                time.sleep(2)  # 频道间隔
            
            print(f"[HTML] ✓ 纽约时报: {len(articles)} 条")
            return articles
        
        except Exception as e:
            print(f"[HTML] ✗ 纽约时报总体失败: {e}")
            return []
    
    def _fetch_nytimes_article(self, url):
        """获取纽约时报文章详情页内容"""
        try:
            response = self.session.get(url, timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取发布时间
            pub_time = datetime.now()
            # 查找 time 标签或日期元素
            time_elem = soup.find('time') or soup.select_one('[data-testid*="date"]')
            if time_elem:
                time_str = time_elem.get_text(strip=True)
                try:
                    pub_time = date_parser.parse(time_str)
                except:
                    pass
            
            # 提取正文内容
            # 纽约时报通常在 <article> 标签中
            article_elem = soup.find('article')
            if not article_elem:
                article_elem = soup.select_one('div[class*="article"], div[id*="article"]')
            
            content = ''
            if article_elem:
                # 移除脚本和样式
                for tag in article_elem.find_all(['script', 'style']):
                    tag.decompose()
                
                # 提取段落
                paragraphs = article_elem.find_all('p')
                texts = []
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if text and len(text) > 5:
                        texts.append(text)
                
                if texts:
                    content = '\n\n'.join(texts)
            
            # 提取图片
            images = []
            for img in soup.find_all('img'):
                src = img.get('src', '').strip()
                if src and src.startswith('http'):
                    alt = img.get('alt', '').strip()
                    images.append({
                        'url': src,
                        'alt': alt or '',
                        'caption': alt or ''
                    })
            
            # 提取视频（通常是iframe）
            videos = []
            for iframe in soup.find_all('iframe'):
                src = iframe.get('src', '').strip()
                if src:
                    videos.append({
                        'url': src,
                        'type': 'iframe',
                        'platform': 'unknown'
                    })
            
            return content, pub_time, images, videos
        
        except Exception as e:
            print(f"    [Error] 获取纽约时报文章失败: {e}")
            return '', datetime.now(), [], []
    
    def fetch_cctv(self):
        """
        央视网爬取（支持新闻和视频）
        URL: https://news.cctv.com/ 及 https://v.cctv.com/
        """
        articles = []
        
        try:
            # 融合新闻网和视频网
            urls = [
                'https://news.cctv.com/',
                'https://v.cctv.com/',
            ]
            
            for base_url in urls:
                source_type = '视频' if 'v.cctv.com' in base_url else '新闻'
                print(f"[HTML] 抓取: 央视网-{source_type}")
                
                try:
                    response = self.session.get(base_url, timeout=15)
                    response.encoding = 'utf-8'
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 央视网的新闻链接通常在特定的结构中
                    # 查找所有新闻链接（包含日期YYYY/MM/DD）
                    news_links = soup.find_all('a', href=re.compile(r'/\d{4}/\d{2}/\d{2}/[A-Z]+'))
                    
                    if not news_links:
                        # 备选选择器
                        news_links = soup.select('div[class*="list"] a, li a')
                    
                    processed_urls = set()
                    
                    for link in news_links[:15]:
                        try:
                            href = link.get('href', '').strip()
                            title = link.get_text(strip=True)
                            
                            if not href or not title or len(title) < 3:
                                continue
                            
                            # 确保是完整URL
                            if not href.startswith('http'):
                                if href.startswith('//'):
                                    href = 'https:' + href
                                elif href.startswith('/'):
                                    href = 'https://news.cctv.com' + href if 'news' in base_url else 'https://v.cctv.com' + href
                                else:
                                    continue
                            
                            # 去重
                            if href in processed_urls:
                                continue
                            processed_urls.add(href)
                            
                            # 获取详情页内容
                            print(f"  [Debug] 获取: {title[:30]}...")
                            content, pub_time, images, videos = self._fetch_cctv_article(href)
                            
                            if content :
                                articles.append({
                                    'title': title[:300],
                                    'summary': content[:500],
                                    'content': content[:15000],
                                    'source_url': href,
                                    'source_name': f'央视网-{source_type}',
                                    'published_at': pub_time,
                                    'image_url': images[0]['url'] if images else None,
                                    'images': images,
                                    'videos': videos,
                                    'category_hint': '资讯',
                                    'country_hint': 'CN',
                                    'fetch_method': 'html_cctv'
                                })
                                print(f"  [Debug] ✓ 成功")
                            
                            time.sleep(1.5)
                        
                        except Exception as e:
                            print(f"  [Debug] 单条失败: {e}")
                            continue
                
                except Exception as e:
                    print(f"[HTML] ✗ 央视网-{source_type}: {e}")
                
                time.sleep(2)
            
            print(f"[HTML] ✓ 央视网: {len(articles)} 条")
            return articles
        
        except Exception as e:
            print(f"[HTML] ✗ 央视网总体失败: {e}")
            return []
    
    def _fetch_cctv_article(self, url):
        """获取央视网文章详情页"""
        try:
            response = self.session.get(url, timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取发布时间
            pub_time = datetime.now()
            # 央视网通常有 span[class*="time"] 包含时间
            time_elem = soup.select_one('span[class*="time"], span.source-time, time')
            if time_elem:
                time_str = time_elem.get_text(strip=True)
                # 匹配 YYYY/MM/DD HH:MM 格式
                match = re.search(r'(\d{4}[年/]\d{2}[月/]\d{2}[日]?)\s*(\d{2}:\d{2})?', time_str)
                if match:
                    try:
                        time_str = match.group(1).replace('年', '/').replace('月', '/').replace('日', '')
                        if match.group(2):
                            time_str += ' ' + match.group(2)
                        pub_time = date_parser.parse(time_str)
                    except:
                        pass
            
            # 提取正文
            # 央视网通常在这些容器中
            content_selectors = [
                'div[id*="content"]',
                'div[class*="body"]',
                'article',
                'div.detail-text',
                'div[class*="article-content"]'
            ]
            
            content = ''
            for selector in content_selectors:
                elem = soup.select_one(selector)
                if elem:
                    for tag in elem.find_all(['script', 'style', 'iframe']):
                        tag.decompose()
                    
                    paragraphs = elem.find_all('p')
                    texts = []
                    for p in paragraphs:
                        text = p.get_text(strip=True)
                        if text and len(text) > 5:
                            texts.append(text)
                    
                    if texts:
                        content = '\n\n'.join(texts)
                        break
            
            # 提取图片和视频（央视网图片通常在 p*.img.cctvpic.com）
            images = []
            videos = []
            
            for img in soup.find_all('img'):
                src = img.get('src', '').strip()
                if src and 'cctvpic' in src:
                    alt = img.get('alt', '').strip()
                    images.append({
                        'url': src,
                        'alt': alt,
                        'caption': alt
                    })
            
            # 视频
            for video in soup.find_all('video'):
                src = video.get('src', '').strip()
                if src:
                    videos.append({
                        'url': src,
                        'type': 'video',
                        'platform': 'cctv'
                    })
                
                for source in video.find_all('source'):
                    src = source.get('src', '').strip()
                    if src:
                        videos.append({
                            'url': src,
                            'type': 'source',
                            'platform': 'cctv'
                        })
            
            return content, pub_time, images, videos
        
        except Exception as e:
            print(f"    [Error] 获取央视网文章失败: {e}")
            return '', datetime.now(), [], []
    
    def fetch_guancha(self):
        """
        观察者网爬取
        URL: https://www.guancha.cn/
        """
        articles = []
        
        try:
            # 国际频道是主要内容来源
            channels = ['america', 'global']
            
            for channel in channels:
                url = f'https://www.guancha.cn/{channel}/'
                print(f"[HTML] 抓取: 观察者网-{channel}")
                
                try:
                    response = self.session.get(url, timeout=15)
                    response.encoding = 'utf-8'
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 观察者网新闻列表通常在特定div中
                    # 查找按日期分组的文章
                    news_items = soup.find_all('a', href=re.compile(r'guancha\.cn/' + channel + r'/\d{4}_\d{2}_\d{2}'))
                    
                    if not news_items:
                        # 备选选择器
                        news_items = soup.select('div[class*="article"] a, ul li a')
                    
                    processed_urls = set()
                    
                    for link in news_items[:15]:
                        try:
                            href = link.get('href', '').strip()
                            title = link.get_text(strip=True)
                            
                            if not href or not title or len(title) < 3:
                                continue
                            
                            if not href.startswith('http'):
                                if href.startswith('/'):
                                    href = 'https://www.guancha.cn' + href
                                else:
                                    continue
                            
                            if href in processed_urls:
                                continue
                            processed_urls.add(href)
                            
                            print(f"  [Debug] 获取: {title[:30]}...")
                            content, pub_time, images, videos = self._fetch_guancha_article(href)
                            
                            if content:
                                articles.append({
                                    'title': title[:300],
                                    'summary': content[:500],
                                    'content': content[:15000],
                                    'source_url': href,
                                    'source_name': '观察者网',
                                    'published_at': pub_time,
                                    'image_url': images[0]['url'] if images else None,
                                    'images': images,
                                    'videos': videos,
                                    'category_hint': channel,
                                    'country_hint': 'CN',
                                    'fetch_method': 'html_guancha'
                                })
                                print(f"  [Debug] ✓ 成功")
                            
                            time.sleep(1.5)
                        
                        except Exception as e:
                            print(f"  [Debug] 单条失败: {e}")
                            continue
                
                except Exception as e:
                    print(f"[HTML] ✗ 观察者网-{channel}: {e}")
                
                time.sleep(2)
            
            print(f"[HTML] ✓ 观察者网: {len(articles)} 条")
            return articles
        
        except Exception as e:
            print(f"[HTML] ✗ 观察者网总体失败: {e}")
            return []
    
    def _fetch_guancha_article(self, url):
        """获取观察者网文章详情页"""
        try:
            response = self.session.get(url, timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 发布时间
            pub_time = datetime.now()
            time_elem = soup.select_one('span[class*="time"], span.article-time, time')
            if time_elem:
                time_str = time_elem.get_text(strip=True)
                try:
                    pub_time = date_parser.parse(time_str)
                except:
                    pass
            
            # 正文
            content_elem = soup.find('article') or soup.select_one('div[class*="article-content"], div[id*="content"]')
            content = ''
            
            if content_elem:
                for tag in content_elem.find_all(['script', 'style']):
                    tag.decompose()
                
                paragraphs = content_elem.find_all('p')
                texts = []
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if text and len(text) > 5:
                        texts.append(text)
                
                if texts:
                    content = '\n\n'.join(texts)
            
            # 图片和视频
            images = []
            videos = []
            
            for img in soup.find_all('img'):
                src = img.get('src', '').strip()
                if src and src.startswith('http'):
                    alt = img.get('alt', '').strip()
                    images.append({
                        'url': src,
                        'alt': alt,
                        'caption': alt
                    })
            
            for iframe in soup.find_all('iframe'):
                src = iframe.get('src', '').strip()
                if src:
                    videos.append({
                        'url': src,
                        'type': 'iframe',
                        'platform': 'unknown'
                    })
            
            return content, pub_time, images, videos
        
        except Exception as e:
            print(f"    [Error] 获取观察者网文章失败: {e}")
            return '', datetime.now(), [], []
    
    def fetch_washingtonpost(self):
        """
        华盛顿邮报爬取
        URL: https://www.washingtonpost.com/
        需要处理反爬虫机制，建议使用高质量 User-Agent
        """
        articles = []
        
        try:
            # 国际和美国新闻是主要频道
            channels = [
                ('https://www.washingtonpost.com/world/', 'world'),
                ('https://www.washingtonpost.com/us-news/', 'us'),
            ]
            
            for url, channel_name in channels:
                print(f"[HTML] 抓取: 华盛顿邮报-{channel_name}")
                
                try:
                    response = self.session.get(url, timeout=15)
                    response.encoding = 'utf-8'
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # WaPo的新闻链接通常是这样的结构
                    news_links = soup.find_all('a', href=re.compile(r'/\d{4}/\d{2}/\d{2}/'))
                    
                    if not news_links:
                        # 备选
                        news_links = soup.select('div[class*="article"], div[class*="story"] a')
                    
                    processed_urls = set()
                    
                    for link in news_links[:15]:
                        try:
                            href = link.get('href', '').strip()
                            title = link.get_text(strip=True)
                            
                            if not href or not title or len(title) < 3:
                                continue
                            
                            if not href.startswith('http'):
                                if href.startswith('/'):
                                    href = 'https://www.washingtonpost.com' + href
                                else:
                                    continue
                            
                            # 去重
                            if href in processed_urls:
                                continue
                            processed_urls.add(href)
                            
                            print(f"  [Debug] 获取: {title[:30]}...")
                            content, pub_time, images, videos = self._fetch_washingtonpost_article(href)
                            
                            if content:
                                articles.append({
                                    'title': title[:300],
                                    'summary': content[:500],
                                    'content': content[:15000],
                                    'source_url': href,
                                    'source_name': '华盛顿邮报',
                                    'published_at': pub_time,
                                    'image_url': images[0]['url'] if images else None,
                                    'images': images,
                                    'videos': videos,
                                    'category_hint': channel_name,
                                    'country_hint': 'US',
                                    'fetch_method': 'html_washingtonpost'
                                })
                                print(f"  [Debug] ✓ 成功")
                            
                            time.sleep(2)  # WaPo需要更长的间隔
                        
                        except Exception as e:
                            print(f"  [Debug] 单条失败: {e}")
                            continue
                
                except Exception as e:
                    print(f"[HTML] ✗ 华盛顿邮报-{channel_name}: {e}")
                
                time.sleep(3)
            
            print(f"[HTML] ✓ 华盛顿邮报: {len(articles)} 条")
            return articles
        
        except Exception as e:
            print(f"[HTML] ✗ 华盛顿邮报总体失败: {e}")
            return []
    
    def _fetch_washingtonpost_article(self, url):
        """获取华盛顿邮报文章详情页"""
        try:
            response = self.session.get(url, timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 检查付费墙
            paywall_signals = ['sign in', 'subscribe', 'login', 'access denied']
            if any(sig in soup.get_text().lower() for sig in paywall_signals):
                print(f"    [Warning] 可能遇到付费墙")
                return '', datetime.now(), [], []
            
            # 发布时间
            pub_time = datetime.now()
            time_elem = soup.find('time') or soup.select_one('[data-testid*="date"]')
            if time_elem:
                try:
                    time_str = time_elem.get_text(strip=True)
                    pub_time = date_parser.parse(time_str)
                except:
                    pass
            
            # 正文
            # WaPo通常在这些容器中
            content_selectors = [
                'article',
                'div[itemprop="articleBody"]',
                'section[data-testid*="body"]',
                'div[class*="article-content"]'
            ]
            
            content = ''
            for selector in content_selectors:
                elem = soup.select_one(selector)
                if elem:
                    for tag in elem.find_all(['script', 'style', 'aside']):
                        tag.decompose()
                    
                    paragraphs = elem.find_all('p')
                    texts = []
                    for p in paragraphs:
                        text = p.get_text(strip=True)
                        if text and len(text) > 5:
                            texts.append(text)
                    
                    if texts:
                        content = '\n\n'.join(texts)
                        break
            
            # 图片和视频
            images = []
            videos = []
            
            for img in soup.find_all('img'):
                src = img.get('src', '').strip()
                if src and src.startswith('http'):
                    alt = img.get('alt', '').strip()
                    images.append({
                        'url': src,
                        'alt': alt,
                        'caption': alt
                    })
            
            for video in soup.find_all('video'):
                src = video.get('src', '').strip()
                if src:
                    videos.append({
                        'url': src,
                        'type': 'video',
                        'platform': 'native'
                    })
                
                for source in video.find_all('source'):
                    src = source.get('src', '').strip()
                    if src:
                        videos.append({
                            'url': src,
                            'type': 'source',
                            'platform': 'native'
                        })
            
            return content, pub_time, images, videos
        
        except Exception as e:
            print(f"    [Error] 获取华盛顿邮报文章失败: {e}")
            return '', datetime.now(), [], []

