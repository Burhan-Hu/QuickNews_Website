import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil import parser as date_parser
import time
import re

class HTMLNewsFetcher:
    """
    国内网站HTML直接抓取（绕过过期RSS）
    """
    
    def __init__(self):
        self.session = requests.Session()
        # 国内网站需要模拟浏览器，否则可能返回403或反爬页面
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
    
    def fetch_xinhua(self):
        """
        新华网-时政频道抓取（基于实际HTML结构）
        目标：http://www.xinhuanet.com/politics/
        """
        url = 'http://www.xinhuanet.com/politics/'
        articles = []
    
        try:
            print(f"[HTML] 抓取: 新华网-时政")
            response = self.session.get(url, timeout=15)
            response.encoding = 'utf-8'
        
            soup = BeautifulSoup(response.text, 'lxml')
        
            # 新华网新闻列表通常在 class="news-list" 或 id="news-list" 的div/ul中
            # 根据你提供的片段，每条新闻是一个 <a> 标签包裹在列表项中
            selectors = [
                '.news-list li',      # 常见列表容器
                '.part-list li',      # 另一种布局
                '.data-list li',      # 数据列表
                '#news-list li',      # ID选择
                '.list-item',         # 通用列表项
                'h3 a[href*="/politics/"]',  # 直接选择政治新闻链接（基于你提供的结构）
                'a[href*=".news.cn/politics/"]'  # 更宽松的匹配
            ]
        
            news_items = []
            for selector in selectors:
                items = soup.select(selector)
                if items:
                    print(f"  [Debug] 使用选择器: {selector}, 找到 {len(items)} 条")
                    news_items = items[:50]  # 取前50条
                    break
        
            if not news_items:
                print("  [Debug] 未找到列表项，尝试通用a标签搜索")
                # 兜底：找所有包含 politics 的链接
                news_items = soup.find_all('a', href=re.compile(r'news\.cn/politics/\d{8}/'))
                news_items = news_items[:50]
        
            for item in news_items:
                try:
                    # 提取链接
                    if item.name == 'a':
                        a_tag = item
                    else:
                        a_tag = item.find('a', href=re.compile(r'news\.cn|xinhuanet\.com'))
                
                    if not a_tag:
                        continue
                
                    title = a_tag.get_text(strip=True)
                    link = a_tag.get('href', '').strip()
                
                    # 清理链接（去除尾部空格等）
                    link = link.replace(' ', '')
                
                    # 补全URL
                    if link.startswith('//'):
                        link = 'http:' + link
                    elif link.startswith('/'):
                        link = 'http://www.xinhuanet.com' + link
                
                    # 过滤无效链接
                    if not link or not re.search(r'(\d{8})/[a-f0-9]+/c\.html$', link):
                        continue
                
                    # 从父元素或meta提取时间（基于你提供的 <meta timestamp="..."> 结构）
                    pub_time = datetime.now()
                
                    # 方法1：查找父元素中的meta标签
                    parent = item.find_parent()
                    if parent:
                        time_meta = parent.find('meta', attrs={'timestamp': True})
                        if time_meta:
                            time_str = time_meta.get('timestamp')
                            try:
                                pub_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M')
                            except:
                                pass
                
                    # 方法2：从链接中提取日期（如 20260318）
                    date_match = re.search(r'/(\d{8})/', link)
                    if date_match:
                        date_str = date_match.group(1)
                        try:
                            pub_time = datetime.strptime(date_str, '%Y%m%d')
                        except:
                            pass
                
                    # 获取详情页全文（关键！）
                    print(f"  [Debug] 正在获取全文: {title[:30]}...")
                    content, article_time, images, videos = self._fetch_article_content(link)

                    # 如果详情页时间更准确，使用详情页时间
                    if article_time != datetime.now():
                        pub_time = article_time

                    if content:  # SQL存储过程会检查长度，这里不做过滤
                        articles.append({
                            'title': title[:300],
                            'summary': content[:500],  # 前500字摘要
                            'content': content[:15000],  # 全文，限制1.5万字
                            'source_url': link,
                            'source_name': '新华网-时政',
                            'published_at': pub_time,
                            'image_url': images[0]['url'] if images else None,  # 第一张图片作为封面
                            'images': images,  # 所有图片列表
                            'videos': videos,  # 所有视频列表
                            'category_hint': 'politics',
                            'country_hint': 'CN',
                            'fetch_method': 'html_xinhua'
                        })
                        print(f"  [Debug] ✓ 成功: {title[:20]}... ({len(content)}字)")
                    else:
                        print(f"  [Debug] ✗ 内容太短或获取失败: {title[:20]}")
                
                    # 礼貌爬取：间隔1秒
                    time.sleep(1)
                
                except Exception as e:
                    print(f"  [Debug] 解析单条失败: {e}")
                    continue
        
            print(f"[HTML] ✓ 新华网-时政: {len(articles)} 条")
            return articles
        
        except Exception as e:
            print(f"[HTML] ✗ 新华网: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _fetch_article_content(self, url):
        """
        抓取详情页正文、图片和视频
        返回: (content文本, pub_time, images列表, videos列表)
        """
        try:
            response = self.session.get(url, timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'lxml')

            # 提取时间
            pub_time = datetime.now()
            time_selectors = [
                '.head-line span', '.info-source', 'span[data-time]',
                '.post-time', 'time', '[id*="time"]', '[class*="date"]'
            ]

            for selector in time_selectors:
                elements = soup.select(selector)
                for element in elements:
                    time_text = element.get_text()
                    match = re.search(r'(\d{4}[-年]\d{2}[-月]\d{2}[^\d]*\d{2}:\d{2})', time_text)
                    if match:
                        try:
                            time_str = match.group(1).replace('年', '-').replace('月', '-').replace('日', ' ')
                            pub_time = datetime.strptime(time_str.strip(), '%Y-%m-%d %H:%M')
                            break
                        except:
                            pass
                if pub_time != datetime.now():
                    break

            # 提取正文 - 更激进的多层级策略
            content_selectors = [
                'article', 'main',
                'div[id*="content"]', 'div[id*="article"]', 'div[id*="story"]',
                'div[class*="content"]', 'div[class*="article"]', 'div[class*="story"]',
                'div[class*="body"]', 'div[class*="text"]', 'div[class*="post"]',
                'div.main', '#p-detail', '.main-content', '#article-content',
                '.content-detail', 'div.article__body', 'div.l-container', 
                'section#body-text', 'div.zn-body__paragraph', 'div.Article__content'
            ]

            content = ''
            
            # 优先级1：尝试所有容器选择器
            for selector in content_selectors:
                try:
                    content_div = soup.select_one(selector)
                    if content_div:
                        for tag in content_div.find_all(['script', 'style', 'iframe', 'aside', 'nav', 'header', 'footer']):
                            tag.decompose()

                        # 提取所有可能的文本内容（p, div, h2-h5, li等）
                        texts = []
                        for elem in content_div.find_all(['p', 'div', 'h2', 'h3', 'h4', 'h5', 'li']):
                            text = elem.get_text(strip=True)
                            # 过滤过短的行
                            if text and len(text) > 3 and not text.endswith((':','：','；', ';')):
                                texts.append(text)
                        
                        # 去重相同的段落（可能因为嵌套导致重复）
                        if texts:
                            seen = set()
                            unique_texts = []
                            for t in texts:
                                if t not in seen:
                                    unique_texts.append(t)
                                    seen.add(t)
                            content = '\n\n'.join(unique_texts)
                            
                        if content and len(content) > 200:
                            break
                except:
                    continue
            
            # 优先级2：如果容器提取失败或内容过短，尝试所有p标签
            if not content or len(content) < 200:
                texts = []
                for p in soup.find_all('p'):
                    text = p.get_text(strip=True)
                    if text and len(text) > 5:
                        texts.append(text)
                if texts:
                    content = '\n\n'.join(texts)
            
            # 优先级3：如果还是没有，尝试所有div[class*=text]或[class*=content]
            if not content or len(content) < 100:
                for selector in ['div[class*="text"]', 'div[class*="content"]', 'div[class*="body"]']:
                    for div in soup.select(selector):
                        for tag in div.find_all(['script', 'style', 'iframe']):
                            tag.decompose()
                        text = div.get_text('\n', strip=True)
                        if text and len(text) > 200:
                            content = text
                            break
                    if content and len(content) > 200:
                        break

            # 提取图片
            images = []
            for img in soup.find_all('img'):
                src = img.get('src', '').strip()
                if src:
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        base_url = '/'.join(url.split('/')[:3])
                        src = base_url + src

                    alt = img.get('alt', '').strip()
                    title = img.get('title', '').strip()

                    if src and not any(skip in src.lower() for skip in ['icon', 'logo', 'avatar', 'button']):
                        images.append({
                            'url': src,
                            'alt': alt or title or '',
                            'caption': alt or title or ''
                        })

            # 提取视频
            videos = []

            # 1. 直接的 <video> 标签
            for video_tag in soup.find_all('video'):
                # 首先检查 src 属性
                src = video_tag.get('src', '').strip()
                if src:
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        base_url = '/'.join(url.split('/')[:3])
                        src = base_url + src
                    videos.append({
                        'url': src,
                        'type': 'direct',
                        'platform': 'unknown'
                    })

                # 检查 <source> 子标签
                for source in video_tag.find_all('source'):
                    src = source.get('src', '').strip()
                    if src:
                        if src.startswith('//'):
                            src = 'https:' + src
                        elif src.startswith('/'):
                            base_url = '/'.join(url.split('/')[:3])
                            src = base_url + src
                        # 检查是否已添加
                        if not any(v['url'] == src for v in videos):
                            videos.append({
                                'url': src,
                                'type': 'source',
                                'platform': 'unknown'
                            })

            # 2. iframe 嵌入视频（YouTube, Vimeo, etc.）
            for iframe in soup.find_all('iframe'):
                src = iframe.get('src', '').strip()
                if src:
                    if 'youtube.com' in src or 'youtu.be' in src:
                        videos.append({
                            'url': src,
                            'type': 'iframe',
                            'platform': 'youtube'
                        })
                    elif 'vimeo.com' in src:
                        videos.append({
                            'url': src,
                            'type': 'iframe',
                            'platform': 'vimeo'
                        })
                    elif 'bilibili.com' in src:
                        videos.append({
                            'url': src,
                            'type': 'iframe',
                            'platform': 'bilibili'
                        })
                    else:
                        videos.append({
                            'url': src,
                            'type': 'iframe',
                            'platform': 'unknown'
                        })

            # 3. 检查常见的视频平台链接和直接视频URL
            video_patterns = [
                (r'youtube\.com/watch\?v=([a-zA-Z0-9_-]+)', 'youtube'),
                (r'youtu\.be/([a-zA-Z0-9_-]+)', 'youtube'),
                (r'vimeo\.com/(\d+)', 'vimeo'),
                (r'bilibili\.com/video/([a-zA-Z0-9]+)', 'bilibili'),
                (r'tiktok\.com/@[^/]+/video/(\d+)', 'tiktok'),
                (r'https?://[^\s<>"{}|\\^`\[\]]*\.(?:mp4|webm|m3u8|flv|mkv|mov|avi)', 'direct_url')
            ]

            for pattern, platform in video_patterns:
                for match in re.finditer(pattern, response.text):
                    if platform == 'youtube':
                        video_id = match.group(1)
                        vid_url = f'https://www.youtube.com/watch?v={video_id}'
                        if not any(v['url'] == vid_url for v in videos):
                            videos.append({
                                'url': vid_url,
                                'type': 'platform_link',
                                'platform': 'youtube',
                                'video_id': video_id
                            })
                    elif platform == 'vimeo':
                        video_id = match.group(1)
                        vid_url = f'https://vimeo.com/{video_id}'
                        if not any(v['url'] == vid_url for v in videos):
                            videos.append({
                                'url': vid_url,
                                'type': 'platform_link',
                                'platform': 'vimeo',
                                'video_id': video_id
                            })
                    elif platform == 'bilibili':
                        video_id = match.group(1)
                        vid_url = f'https://www.bilibili.com/video/{video_id}'
                        if not any(v['url'] == vid_url for v in videos):
                            videos.append({
                                'url': vid_url,
                                'type': 'platform_link',
                                'platform': 'bilibili',
                                'video_id': video_id
                            })
                    elif platform == 'direct_url':
                        # 直接视频URL
                        vid_url = match.group(0)
                        if not any(v['url'] == vid_url for v in videos):
                            videos.append({
                                'url': vid_url,
                                'type': 'direct_url',
                                'platform': 'unknown'
                            })

            return content, pub_time, images, videos

        except Exception as e:
            print(f"    [Debug] 详情页失败: {e}")
            return '', datetime.now(), [], []

    def _normalize_link(self, link, base_url):
        if not link:
            return ''
        link = link.strip()
        if link.startswith('//'):
            return 'https:' + link
        if link.startswith('/'):
            return base_url.rstrip('/') + link
        return link

    def _gather_article_links(self, soup, selectors, base_url, href_regex=None, limit=15):
        links = []
        for sel in selectors:
            for node in soup.select(sel):
                a = node if node.name == 'a' else node.find('a')
                if not a:
                    continue
                href = a.get('href', '').strip()
                href = self._normalize_link(href, base_url)
                if not href:
                    continue
                if href_regex and not re.search(href_regex, href):
                    continue
                if href in links:
                    continue
                links.append(href)
                if len(links) >= limit:
                    return links
        return links

    def fetch_scmp(self):
        """南华早报SCMP中国新闻抓取"""
        url = 'https://www.scmp.com/news/china'
        print(f"[HTML] 抓取: SCMP-China")
        try:
            response = self.session.get(url, timeout=20)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'lxml')

            candidate = self._gather_article_links(
                soup,
                selectors=['.story-card__heading a', '.river-item__text a', 'a[href*="/article/"]'],
                base_url='https://www.scmp.com',
                href_regex=r'https?://www\.scmp\.com/.+',
                limit=80
            )

            articles = []
            for link in candidate:
                try:
                    print(f"  [Debug] SCMP 获取: {link}")
                    content, pub_time, images, videos = self._fetch_article_content(link)
                    if content:
                        title = ''
                        m = re.search(r'/([^/]+)$', link)
                        if m:
                            title = m.group(1).replace('-', ' ')
                        articles.append({
                            'title': title[:300] or 'SCMP',
                            'summary': content[:500],
                            'content': content[:15000],
                            'source_url': link,
                            'source_name': 'SCMP',
                            'published_at': pub_time,
                            'image_url': None,
                            'category_hint': 'international',
                            'country_hint': 'HK',
                            'fetch_method': 'html_scmp'
                        })
                        print(f"  [Debug] SCMP ✓ 成功: {link}")
                    else:
                        print(f"  [Debug] SCMP ✗ 内容太短: {link}")
                except Exception as e:
                    print(f"  [Debug] SCMP 失败: {e}")
                    continue

            print(f"[HTML] ✓ SCMP-China: {len(articles)} 条")
            return articles
        except Exception as e:
            print(f"[HTML] ✗ SCMP: {e}")
            return []

    def fetch_cnn(self):
        """CNN世界新闻抓取"""
        url = 'https://edition.cnn.com/world'
        print(f"[HTML] 抓取: CNN-World")
        try:
            response = self.session.get(url, timeout=20)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'lxml')

            candidate = self._gather_article_links(
                soup,
                selectors=['.cd__headline a', 'h3 a', 'a[href*="/2026/"]'],
                base_url='https://edition.cnn.com',
                href_regex=r'https?://edition\.cnn\.com/.+',
                limit=80
            )

            articles = []
            for link in candidate:
                try:
                    print(f"  [Debug] CNN 获取: {link}")
                    content, pub_time, images, videos = self._fetch_article_content(link)
                    if content:
                        title = ''
                        m = re.search(r'/([^/]+)\.?html?$', link)
                        if m:
                            title = m.group(1).replace('-', ' ')
                        articles.append({
                            'title': title[:300] or 'CNN',
                            'summary': content[:500],
                            'content': content[:15000],
                            'source_url': link,
                            'source_name': 'CNN',
                            'published_at': pub_time,
                            'image_url': images[0]['url'] if images else None,
                            'images': images,
                            'videos': videos,
                            'category_hint': 'international',
                            'country_hint': 'US',
                            'fetch_method': 'html_cnn'
                        })
                        print(f"  [Debug] CNN ✓ 成功: {link}")
                    else:
                        print(f"  [Debug] CNN ✗ 内容太短: {link}")
                except Exception as e:
                    print(f"  [Debug] CNN 失败: {e}")
                    continue

            print(f"[HTML] ✓ CNN-World: {len(articles)} 条")
            return articles
        except Exception as e:
            print(f"[HTML] ✗ CNN: {e}")
            return []


    def fetch_cctv(self):
        """
        央视网爬取（支持新闻和视频）
        URL: https://news.cctv.com/ 及 https://v.cctv.com/
        """
        articles = []
        
        try:
            urls = [
                'https://news.cctv.com/',
                'https://v.cctv.com/',
            ]
            
            for base_url in urls:
                source_type = '视频' if 'v.cctv.com' in base_url else '新闻'
                print(f"[HTML] 抓取: 央视网-{source_type}")
                
                try:
                    response = self.session.get(base_url, timeout=20)
                    response.encoding = 'utf-8'
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    news_links = soup.find_all('a', href=re.compile(r'/\d{4}/\d{2}/\d{2}/[A-Z]+'))
                    
                    if not news_links:
                        news_links = soup.select('div[class*="list"] a, li a')
                    
                    processed_urls = set()
                    
                    for link in news_links[:80]:
                        try:
                            href = link.get('href', '').strip()
                            title = link.get_text(strip=True)
                            
                            if not href or not title or len(title) < 3:
                                continue
                            
                            if not href.startswith('http'):
                                if href.startswith('//'):
                                    href = 'https:' + href
                                elif href.startswith('/'):
                                    href = 'https://news.cctv.com' + href if 'news' in base_url else 'https://v.cctv.com' + href
                                else:
                                    continue
                            
                            if href in processed_urls:
                                continue
                            processed_urls.add(href)
                            
                            print(f"  [Debug] 获取: {title[:30]}...")
                            content, pub_time, images, videos = self._fetch_cctv_article(href)
                            
                            if content and len(content) > 50:
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
            response = self.session.get(url, timeout=15)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            pub_time = datetime.now()
            time_elem = soup.select_one('span[class*="time"], span.source-time, time')
            if time_elem:
                time_str = time_elem.get_text(strip=True)
                match = re.search(r'(\d{4}[年/]\d{2}[月/]\d{2}[日]?)\s*(\d{2}:\d{2})?', time_str)
                if match:
                    try:
                        time_str = match.group(1).replace('年', '/').replace('月', '/').replace('日', '')
                        if match.group(2):
                            time_str += ' ' + match.group(2)
                        pub_time = date_parser.parse(time_str)
                    except:
                        pass
            
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

    def fetch_aljazeera(self):
        """
        Al Jazeera 英文新闻爬取
        URL: https://www.aljazeera.com/
        """
        articles = []
        categories = ['news', 'americas', 'asia']
        
        try:
            for category in categories:
                url = f'https://www.aljazeera.com/{category}/'
                print(f"[HTML] 抓取: Al Jazeera-{category}")
                
                try:
                    response = self.session.get(url, timeout=15)
                    response.encoding = 'utf-8'
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 查找新闻链接
                    article_links = soup.find_all('a', href=re.compile(r'/news/[a-z0-9\-]+/'))
                    
                    if not article_links:
                        article_links = soup.select('article a[href*="/news/"], h2 a[href*="/news/"]')
                    
                    processed_urls = set()
                    
                    for link in article_links[:80]:
                        try:
                            href = link.get('href', '').strip()
                            title = link.get_text(strip=True)
                            
                            if not href or not title or len(title) < 5:
                                continue
                            
                            if not href.startswith('http'):
                                if href.startswith('/'):
                                    href = 'https://www.aljazeera.com' + href
                                else:
                                    continue
                            
                            if href in processed_urls:
                                continue
                            processed_urls.add(href)
                            
                            print(f"  [Debug] 获取: {title[:30]}...")
                            content, pub_time, images, videos = self._fetch_aljazeera_article(href)
                            
                            if content:
                                articles.append({
                                    'title': title[:300],
                                    'summary': content[:500],
                                    'content': content[:15000],
                                    'source_url': href,
                                    'source_name': 'Al Jazeera',
                                    'published_at': pub_time,
                                    'image_url': images[0]['url'] if images else None,
                                    'images': images,
                                    'videos': videos,
                                    'category_hint': category,
                                    'country_hint': 'US',
                                    'fetch_method': 'html_aljazeera'
                                })
                                print(f"  [Debug] ✓ 成功 ({len(content)}字)")
                            else:
                                print(f"  [Debug] ✗ 内容不足: {len(content) if content else 0}字")
                            
                            time.sleep(1.5)
                        
                        except Exception as e:
                            print(f"  [Debug] 单条失败: {e}")
                            continue
                
                except Exception as e:
                    print(f"[HTML] ✗ Al Jazeera-{category}: {e}")
                
                time.sleep(2)
            
            print(f"[HTML] ✓ Al Jazeera: {len(articles)} 条")
            return articles
        
        except Exception as e:
            print(f"[HTML] ✗ Al Jazeera 总体失败: {e}")
            return []

    def _fetch_aljazeera_article(self, url):
        """获取Al Jazeera文章详情页"""
        try:
            response = self.session.get(url, timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            pub_time = datetime.now()
            time_elem = soup.find('time')
            if time_elem:
                datetime_attr = time_elem.get('datetime')
                if datetime_attr:
                    try:
                        pub_time = date_parser.parse(datetime_attr)
                    except:
                        pass
            
            # 提取正文 - 尝试多个选择器
            content = ''
            content_elem = None
            
            # 优先级1: article标签
            content_elem = soup.find('article')
            if content_elem:
                for tag in content_elem.find_all(['script', 'style', 'aside']):
                    tag.decompose()
                paragraphs = content_elem.find_all('p')
                if paragraphs:
                    content = '\n\n'.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
            
            # 优先级2: 如果article没有内容，尝试div[class*="content"]
            if not content:
                for selector in ['div[class*="article-content"]', '[class*="story-body"]', '[class*="body-content"]', 'main', '[role="main"]']:
                    content_elem = soup.select_one(selector)
                    if content_elem:
                        for tag in content_elem.find_all(['script', 'style', 'aside']):
                            tag.decompose()
                        paragraphs = content_elem.find_all('p')
                        if paragraphs:
                            content = '\n\n'.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
                            if content:
                                break
            
            # 优先级3: 如果还是没有，尝试所有p标签
            if not content:
                paragraphs = soup.find_all('p')
                if paragraphs:
                    content = '\n\n'.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
            
            # 提取图片
            images = []
            for img in soup.find_all('img'):
                src = img.get('src', '').strip()
                if src and src.startswith('http'):
                    alt = img.get('alt', '').strip()
                    if not any(x in src.lower() for x in ['logo', 'icon']):
                        images.append({
                            'url': src,
                            'alt': alt or '',
                            'caption': alt or ''
                        })
            
            # 提取视频
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
            print(f"    [Error] 获取Al Jazeera文章失败: {e}")
            return '', datetime.now(), [], []

    def fetch_globaltimes(self):
        """
        环球时报中文新闻爬取
        URL: https://www.globaltimes.cn/
        """
        articles = []
        channels = ['world', 'china']
        
        try:
            for channel in channels:
                if channel == 'world':
                    url = 'https://www.globaltimes.cn/world/index.html'
                elif channel == 'china':
                    url = 'https://www.globaltimes.cn/china/index.html'
                else:
                    continue
                
                print(f"[HTML] 抓取: 环球时报-{channel}")
                
                try:
                    response = self.session.get(url, timeout=15)
                    response.encoding = 'utf-8'
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 查找新闻链接
                    article_links = soup.find_all('a', href=re.compile(r'/page/\d{6}/\d+\.shtml'))
                    
                    if not article_links:
                        article_links = soup.select('a[href*="/page/"]')
                    
                    processed_urls = set()
                    
                    for link in article_links[:80]:
                        try:
                            href = link.get('href', '').strip()
                            title = link.get_text(strip=True)
                            
                            if not href or not title or len(title) < 5:
                                continue
                            
                            if not href.startswith('http'):
                                if href.startswith('/'):
                                    href = 'https://www.globaltimes.cn' + href
                                else:
                                    continue
                            
                            if href in processed_urls:
                                continue
                            processed_urls.add(href)
                            
                            print(f"  [Debug] 获取: {title[:30]}...")
                            content, pub_time, images, videos = self._fetch_globaltimes_article(href)
                            
                            if content and len(content) > 100:
                                articles.append({
                                    'title': title[:300],
                                    'summary': content[:500],
                                    'content': content[:15000],
                                    'source_url': href,
                                    'source_name': '环球时报',
                                    'published_at': pub_time,
                                    'image_url': images[0]['url'] if images else None,
                                    'images': images,
                                    'videos': videos,
                                    'category_hint': channel,
                                    'country_hint': 'CN',
                                    'fetch_method': 'html_globaltimes'
                                })
                                print(f"  [Debug] ✓ 成功 ({len(content)}字)")
                            else:
                                print(f"  [Debug] ✗ 内容不足: {len(content) if content else 0}字")
                            
                            time.sleep(1.5)
                        
                        except Exception as e:
                            print(f"  [Debug] 单条失败: {e}")
                            continue
                
                except Exception as e:
                    print(f"[HTML] ✗ 环球时报-{channel}: {e}")
                
                time.sleep(2)
            
            print(f"[HTML] ✓ 环球时报: {len(articles)} 条")
            return articles
        
        except Exception as e:
            print(f"[HTML] ✗ 环球时报总体失败: {e}")
            return []

    def _fetch_globaltimes_article(self, url):
        """获取环球时报文章详情页"""
        try:
            response = self.session.get(url, timeout=15)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            pub_time = datetime.now()
            # 查找时间元素
            for elem in soup.select('span[class*="date"], [class*="pubTime"], [class*="time"], time'):
                text = elem.get_text(strip=True)
                match = re.search(r'(\d{4}[年-]\d{2}[月-]\d{2}[日]?)\s*(\d{2}:\d{2})?', text)
                if match:
                    try:
                        time_str = match.group(1).replace('年', '-').replace('月', '-').replace('日', '')
                        if match.group(2):
                            time_str += ' ' + match.group(2)
                        pub_time = date_parser.parse(time_str)
                        break
                    except:
                        pass
            
            # 提取正文 - 激进的多层级策略（类似_fetch_article_content）
            content = ''
            
            # 优先级1：尝试所有可能的容器选择器
            content_selectors = [
                'article', 'main',
                'div[id*="content"]', 'div[id*="article"]', 'div[id*="story"]',
                'div[class*="content"]', 'div[class*="article"]', 'div[class*="story"]',
                'div[class*="body"]', 'div[class*="text"]', 'div[class*="post"]',
                '[class*="article-content"]', '[class*="story-body"]', '[class*="article-text"]',
                '[class*="txt"]', '[role="main"]'
            ]
            
            for selector in content_selectors:
                try:
                    content_div = soup.select_one(selector)
                    if content_div:
                        # 清理不要的元素
                        for tag in content_div.find_all(['script', 'style', 'iframe', 'aside', 'nav', 'header', 'footer']):
                            tag.decompose()
                        
                        # 提取所有可能的文本
                        texts = []
                        for elem in content_div.find_all(['p', 'div', 'h2', 'h3', 'h4', 'h5', 'li', 'span']):
                            text = elem.get_text(strip=True)
                            if text and len(text) > 3 and not text.endswith((':', '：', '；', ';', '。', '。')):
                                texts.append(text)
                        
                        if texts:
                            seen = set()
                            unique_texts = []
                            for t in texts:
                                if t not in seen:
                                    unique_texts.append(t)
                                    seen.add(t)
                            content = '\n\n'.join(unique_texts)
                        
                        if content and len(content) > 100:
                            break
                except:
                    continue
            
            # 优先级2：如果容器提取失败，尝试所有p标签
            if not content or len(content) < 100:
                texts = []
                for p in soup.find_all('p'):
                    text = p.get_text(strip=True)
                    if text and len(text) > 5:
                        texts.append(text)
                if texts:
                    content = '\n\n'.join(texts)
            
            # 优先级3：最后的兜底：所有文本
            if not content or len(content) < 50:
                body = soup.find('body')
                if body:
                    for tag in body.find_all(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                        tag.decompose()
                    text = body.get_text('\n', strip=True)
                    # 取前3000字（过滤掉导航等）
                    lines = [l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) > 5]
                    if lines:
                        content = '\n\n'.join(lines[:100])  # 取前100行
            
            # 提取图片
            images = []
            for img in soup.find_all('img'):
                src = img.get('src', '').strip()
                if src:
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = 'https://www.globaltimes.cn' + src
                    
                    alt = img.get('alt', '').strip()
                    if not any(x in src.lower() for x in ['logo', 'icon', 'gray_play']):
                        images.append({
                            'url': src,
                            'alt': alt or '',
                            'caption': alt or ''
                        })
            
            # 提取视频
            videos = []
            for video in soup.find_all('iframe'):
                src = video.get('src', '').strip()
                if src and any(x in src for x in ['youtube', 'youku', 'video']):
                    videos.append({
                        'url': src,
                        'type': 'iframe',
                        'platform': 'unknown'
                    })
            
            return content, pub_time, images, videos
        
        except Exception as e:
            print(f"    [Error] 获取环球时报文章失败: {e}")
            return '', datetime.now(), [], []

    def fetch_all_domestic(self):
        """抓取所有国内外源"""
        all_articles = []
        
        # 新华网
        all_articles.extend(self.fetch_xinhua())

        # 南华早报
        all_articles.extend(self.fetch_scmp())

        # CNN
        all_articles.extend(self.fetch_cnn())

        # 纽约时报
        all_articles.extend(self.fetch_nytimes())

        # 央视网
        all_articles.extend(self.fetch_cctv())

        # Al Jazeera
        all_articles.extend(self.fetch_aljazeera())

        # 环球时报
        all_articles.extend(self.fetch_globaltimes())
        
        return all_articles
    # ========== 特定网站HTML抓取（替代RSS） ==========
    
    def fetch_sciencedaily(self):
        """
        ScienceDaily HTML抓取 - 重写版
        网址: https://www.sciencedaily.com/news/
        """
        url = 'https://www.sciencedaily.com/news/'
        print(f"[HTML] 抓取: ScienceDaily")
        
        try:
            response = self.session.get(url, timeout=15, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            articles = []
            # 尝试多种选择器找新闻列表
            news_links = []
            
            # 方法1: 查找所有指向 /releases/ 的链接（ScienceDaily文章URL模式）
            for a in soup.find_all('a', href=re.compile(r'/releases/\d{4}/\d{2}/')):
                title = a.get_text(strip=True)
                if title and len(title) > 10:
                    news_links.append((title, a.get('href', '')))
            
            # 方法2: 查找 h2/h3 下的链接
            if not news_links:
                for a in soup.select('h2 a, h3 a, .headline a, .title a'):
                    title = a.get_text(strip=True)
                    href = a.get('href', '')
                    if title and len(title) > 10 and '/releases/' in href:
                        news_links.append((title, href))
            
            # 去重
            seen = set()
            unique_links = []
            for title, href in news_links[:20]:
                if href not in seen:
                    seen.add(href)
                    unique_links.append((title, href))
            
            print(f"  [Debug] 找到 {len(unique_links)} 条新闻链接")
            
            for title, href in unique_links:
                try:
                    if not href.startswith('http'):
                        link = 'https://www.sciencedaily.com' + href
                    else:
                        link = href
                    
                    print(f"  [ScienceDaily] 获取: {title[:50]}...")
                    
                    # 抓取详情页
                    article_resp = self.session.get(link, timeout=10, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    })
                    article_resp.encoding = 'utf-8'
                    article_soup = BeautifulSoup(article_resp.text, 'lxml')
                    
                    # 提取时间
                    pub_time = datetime.now()
                    # ScienceDaily时间格式: March 24, 2026
                    date_elem = article_soup.find('dt', string='Date:')
                    if date_elem:
                        date_text = date_elem.find_next('dd').get_text(strip=True) if date_elem.find_next('dd') else ''
                        if date_text:
                            try:
                                pub_time = date_parser.parse(date_text)
                            except:
                                pass
                    
                    # 提取正文 - 多种选择器尝试
                    content = ''
                    selectors = ['#text', '#story_content', '.lead', '[itemprop="articleBody"]', '.article-content']
                    for sel in selectors:
                        content_elem = article_soup.select_one(sel)
                        if content_elem:
                            for tag in content_elem.find_all(['script', 'style', 'aside']):
                                tag.decompose()
                            paragraphs = content_elem.find_all('p')
                            texts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
                            content = '\n\n'.join(texts)
                            if len(content) > 200:
                                break
                    
                    # 提取图片
                    images = []
                    for img in article_soup.select('#text img, .lead img, [itemprop="articleBody"] img'):
                        src = img.get('src', '')
                        if src and not src.endswith('.gif'):
                            if src.startswith('/'):
                                src = 'https://www.sciencedaily.com' + src
                            images.append({'url': src, 'alt': img.get('alt', ''), 'caption': img.get('alt', '')})
                    
                    if content and len(content) > 200:
                        articles.append({
                            'title': title[:300],
                            'content': content[:20000],
                            'source_url': link,
                            'source_name': 'ScienceDaily',
                            'published_at': pub_time,
                            'image_url': images[0]['url'] if images else None,
                            'images': images,
                            'category_hint': 'science',
                            'country_hint': 'US',
                            'fetch_method': 'html_sciencedaily'
                        })
                        print(f"    ✓ {len(content)} 字, {len(images)} 图")
                    else:
                        print(f"    ✗ 内容太短: {len(content)} 字")
                    
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"    ✗ 失败: {str(e)[:40]}")
                    continue
            
            print(f"[HTML] ✓ ScienceDaily: {len(articles)} 条")
            return articles
            
        except Exception as e:
            print(f"[HTML] ✗ ScienceDaily: {str(e)[:50]}")
            return []
    def _fetch_sputnik_article(self, url):
        """获取俄罗斯卫星通讯社文章详情页 - 根据实际HTML结构调整"""
        try:
            response = self.session.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'lxml')
            
            # 提取时间
            pub_time = datetime.now()
            time_elem = soup.find('time') or soup.select_one('[datetime]')
            if time_elem and time_elem.get('datetime'):
                try:
                    pub_time = date_parser.parse(time_elem['datetime'])
                except:
                    pass
            
            # ===== 关键修复：根据提供的HTML结构提取正文 =====
            content = ''
            
            # 方法1: 查找article__body容器，提取所有文本块（包括普通文本和引用）
            article_body = soup.select_one('.article__body')
            if article_body:
                # 查找所有文本块: .article__text (普通文本) 和 .article__quote-text (引用)
                text_blocks = article_body.select('.article__text, .article__quote-text')
                if text_blocks:
                    texts = []
                    for block in text_blocks:
                        text = block.get_text(strip=True)
                        # 过滤空文本和过短文本
                        if text and len(text) > 3:
                            texts.append(text)
                    # 用双换行分隔，保持段落结构
                    content = '\n\n'.join(texts)
                    print(f"    [Debug] 从article__body提取到 {len(texts)} 个文本块")
            
            # 方法2: 如果方法1失败，尝试直接查找所有article__text（兼容旧结构）
            if not content or len(content) < 100:
                text_blocks = soup.select('.article__text')
                if text_blocks:
                    texts = [block.get_text(strip=True) for block in text_blocks if block.get_text(strip=True)]
                    content = '\n\n'.join(texts)
            
            # 方法3: 兜底方案 - 使用通用选择器
            if not content or len(content) < 100:
                selectors = [
                    '.b-article__text',
                    '[itemprop="articleBody"]',
                    '.article-body',
                    'article'
                ]
                for sel in selectors:
                    content_elem = soup.select_one(sel)
                    if content_elem:
                        for tag in content_elem.find_all(['script', 'style', 'nav', 'aside']):
                            tag.decompose()
                        paragraphs = content_elem.find_all(['p', 'div'])
                        texts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
                        if texts:
                            content = '\n\n'.join(texts)
                            break
            
            # ===== 提取图片 - 根据HTML中的img标签结构 =====
            images = []
            # 文章图片通常在.article__body内的img标签，或在article__block[data-type="article"]
            for img in soup.select('.article__body img, .article__image img, .b-article__text img'):
                src = img.get('src', '').strip()
                if not src:
                    continue
                
                # 处理协议相对URL和相对路径
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = 'https://sputniknews.cn' + src
                
                alt = img.get('alt', '').strip()
                title = img.get('title', '').strip()
                
                # 过滤掉图标、logo、小图片
                if any(x in src.lower() for x in ['icon', 'logo', 'avatar', 'button', 'svg', 'share', 'more']):
                    continue
                
                # 过滤重复URL（srcset中的不同尺寸）
                if not any(i['url'] == src for i in images):
                    images.append({
                        'url': src,
                        'alt': alt,
                        'caption': title or alt
                    })
            
            # ===== 提取视频 =====
            videos = []
            # 查找iframe嵌入视频
            for iframe in soup.find_all('iframe'):
                src = iframe.get('src', '').strip()
                if src:
                    videos.append({
                        'url': src,
                        'type': 'iframe',
                        'platform': 'unknown'
                    })
            
            # 查找video标签
            for video in soup.find_all('video'):
                src = video.get('src', '').strip()
                if src:
                    videos.append({
                        'url': src,
                        'type': 'video',
                        'platform': 'sputnik'
                    })
                # 检查source子标签
                for source in video.find_all('source'):
                    src = source.get('src', '').strip()
                    if src and not any(v['url'] == src for v in videos):
                        videos.append({
                            'url': src,
                            'type': 'source',
                            'platform': 'sputnik'
                        })
            
            return content, pub_time, images, videos
            
        except Exception as e:
            print(f"    [Error] 获取俄罗斯卫星通讯社文章失败: {str(e)[:100]}")
            return '', datetime.now(), [], []
            
    def fetch_sputnik(self):
        """
        俄罗斯卫星通讯社 HTML抓取 - 整合版
        网址: https://sputniknews.cn/
        正文结构: .article__body 内包含多个 .article__text 和 .article__quote-text
        """
        urls = [
            'https://sputniknews.cn/politics/',
            'https://sputniknews.cn/world/',
            'https://sputniknews.cn/economy/',
        ]
        
        all_articles = []
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        for url in urls:
            try:
                print(f"[HTML] 抓取: 俄罗斯卫星通讯社 - {url.split('/')[-2]}")
                
                response = session.get(url, timeout=15)
                response.raise_for_status()
                response.encoding = 'utf-8'
                
                soup = BeautifulSoup(response.text, 'lxml')
                
                # 查找文章链接 - 俄罗斯卫星通讯社中文版的URL模式
                news_links = []
                for a in soup.find_all('a', href=re.compile(r'/\d{8}/')):
                    title = a.get_text(strip=True)
                    href = a.get('href', '')
                    if title and len(title) > 10:
                        if href.startswith('/'):
                            href = 'https://sputniknews.cn' + href
                        elif not href.startswith('http'):
                            continue
                        news_links.append((title, href))
                
                # 去重
                seen = set()
                unique_links = []
                for title, href in news_links[:10]:
                    if href not in seen:
                        seen.add(href)
                        unique_links.append((title, href))
                
                print(f"  [Debug] {url.split('/')[-2]} 栏目找到 {len(unique_links)} 条")
                
                articles = []
                
                for title, href in unique_links:
                    try:
                        print(f"  [Sputnik] 获取: {title[:50]}...")
                        
                        # ===== 内嵌详情页抓取逻辑 =====
                        article_resp = session.get(href, timeout=10)
                        article_resp.encoding = 'utf-8'
                        article_soup = BeautifulSoup(article_resp.text, 'lxml')
                        
                        # 提取时间
                        pub_time = datetime.now()
                        # 优先从meta标签提取（如用户提供的格式）
                        time_meta = article_soup.find('meta', attrs={'timestamp': True})
                        if time_meta:
                            time_str = time_meta.get('timestamp')
                            try:
                                pub_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M')
                            except:
                                pass
                        
                        # 如果没从meta获取到，尝试time标签
                        if pub_time == datetime.now():
                            time_elem = article_soup.find('time') or article_soup.select_one('[datetime]')
                            if time_elem and time_elem.get('datetime'):
                                try:
                                    pub_time = date_parser.parse(time_elem['datetime'])
                                except:
                                    pass
                        
                        # 提取正文 - 根据用户提供的HTML结构
                        content = ''
                        
                        # 方法1: 查找article__body容器，提取所有文本块
                        article_body = article_soup.select_one('.article__body')
                        if article_body:
                            # 提取所有文本块: .article__text (普通文本) 和 .article__quote-text (引用)
                            text_blocks = article_body.select('.article__text, .article__quote-text')
                            if text_blocks:
                                texts = []
                                for block in text_blocks:
                                    text = block.get_text(strip=True)
                                    if text and len(text) > 3:
                                        texts.append(text)
                                content = '\n\n'.join(texts)
                        
                        # 方法2: 如果方法1失败，尝试直接查找所有article__text
                        if not content or len(content) < 100:
                            text_blocks = article_soup.select('.article__text')
                            if text_blocks:
                                texts = [block.get_text(strip=True) for block in text_blocks if block.get_text(strip=True)]
                                content = '\n\n'.join(texts)
                        
                        # 方法3: 兜底方案
                        if not content or len(content) < 100:
                            selectors = ['.b-article__text', '[itemprop="articleBody"]', 'article']
                            for sel in selectors:
                                content_elem = article_soup.select_one(sel)
                                if content_elem:
                                    for tag in content_elem.find_all(['script', 'style', 'nav', 'aside']):
                                        tag.decompose()
                                    paragraphs = content_elem.find_all('p')
                                    texts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
                                    if texts:
                                        content = '\n\n'.join(texts)
                                        break
                        
                        # 提取图片
                        images = []
                        # 从article__body内查找所有img（排除分享按钮等小图标）
                        for img in article_soup.select('.article__body img, .b-article__text img'):
                            src = img.get('src', '').strip()
                            if not src:
                                continue
                            
                            # 处理URL
                            if src.startswith('//'):
                                src = 'https:' + src
                            elif src.startswith('/'):
                                src = 'https://sputniknews.cn' + src
                            
                            # 过滤掉图标和按钮图片
                            if any(x in src.lower() for x in ['icon', 'logo', 'avatar', 'button', 'share', 'more', 'svg']):
                                continue
                            
                            alt = img.get('alt', '').strip()
                            title = img.get('title', '').strip()
                            
                            # 避免重复
                            if not any(i['url'] == src for i in images):
                                images.append({
                                    'url': src,
                                    'alt': alt,
                                    'caption': title or alt
                                })
                        
                        # 提取视频
                        videos = []
                        # 查找iframe嵌入
                        for iframe in article_soup.find_all('iframe'):
                            src = iframe.get('src', '').strip()
                            if src:
                                videos.append({'url': src, 'type': 'iframe', 'platform': 'unknown'})
                        
                        # 查找video标签
                        for video in article_soup.find_all('video'):
                            src = video.get('src', '').strip()
                            if src:
                                videos.append({'url': src, 'type': 'video', 'platform': 'sputnik'})
                            for source in video.find_all('source'):
                                src = source.get('src', '').strip()
                                if src and not any(v['url'] == src for v in videos):
                                    videos.append({'url': src, 'type': 'source', 'platform': 'sputnik'})
                        
                        # 保存数据
                        if content:
                            articles.append({
                                'title': title[:300],
                                'content': content[:20000],
                                'source_url': href,
                                'source_name': '俄罗斯卫星通讯社',
                                'published_at': pub_time,
                                'image_url': images[0]['url'] if images else None,
                                'images': images,
                                'videos': videos,
                                'category_hint': 'international',
                                'country_hint': 'RU',
                                'fetch_method': 'html_sputnik'
                            })
                            print(f"    ✓ 获取成功 ({len(content)}字, {len(images)}图, {len(videos)}视频)")
                        else:
                            print(f"    ✗ 内容为空")
                        
                        time.sleep(1)
                        
                    except Exception as e:
                        print(f"    ✗ 失败: {str(e)[:50]}")
                        continue
                
                all_articles.extend(articles)
                time.sleep(1)
                
            except Exception as e:
                print(f"[HTML] ✗ 俄罗斯卫星通讯社 {url}: {str(e)[:50]}")
                continue
        
        print(f"[HTML] ✓ 俄罗斯卫星通讯社: 共 {len(all_articles)} 条")
        return all_articles

    def fetch_nytimes_cn(self):
        """
        纽约时报-中文 HTML抓取 - 修正版
        网址: https://cn.nytimes.com/
        正文结构: .article-paragraph (根据你提供的HTML片段)
        """
        urls = [
            'https://cn.nytimes.com/china/',
            'https://cn.nytimes.com/world/',
            'https://cn.nytimes.com/business/',
            'https://cn.nytimes.com/technology/',
        ]
        
        all_articles = []
        
        for url in urls:
            try:
                print(f"[HTML] 抓取: 纽约时报-中文 - {url.split('/')[-2]}")
                
                response = self.session.get(url, timeout=15, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                response.raise_for_status()
                response.encoding = 'utf-8'
                
                soup = BeautifulSoup(response.text, 'lxml')
                
                articles = []
                news_links = []
                
                # 查找文章链接 - 纽约时报中文版的URL模式: /category/YYYYMMDD/article-title/
                for a in soup.find_all('a', href=re.compile(r'/[a-z]+/\d{8}/[a-z0-9\-]+/$')):
                    title = a.get_text(strip=True)
                    href = a.get('href', '')
                    if title and len(title) > 10:
                        if href.startswith('/'):
                            href = 'https://cn.nytimes.com' + href
                        elif not href.startswith('https'):
                            continue
                        news_links.append((title, href))
                
                # 去重
                seen = set()
                unique_links = []
                for title, href in news_links[:8]:
                    if href not in seen and not any(x in href for x in ['/slideshow/', '/video/', '/author/']):
                        seen.add(href)
                        unique_links.append((title, href))
                
                print(f"  [Debug] {url.split('/')[-2]} 栏目找到 {len(unique_links)} 条")
                
                for title, href in unique_links:
                    try:
                        print(f"  [NYTimes-CN] 获取: {title[:50]}...")
                        
                        article_resp = self.session.get(href, timeout=10, headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        })
                        article_resp.encoding = 'utf-8'
                        article_soup = BeautifulSoup(article_resp.text, 'lxml')
                        
                        # 提取时间
                        pub_time = datetime.now()
                        time_elem = article_soup.find('time') or article_soup.select_one('[datetime]')
                        if time_elem and time_elem.get('datetime'):
                            try:
                                pub_time = date_parser.parse(time_elem['datetime'])
                            except:
                                pass
                        
                        # 提取正文 - 根据你提供的HTML结构使用 .article-paragraph
                        content = ''
                        
                        # 方法1: 使用你提供的 .article-paragraph 类
                        paragraphs = article_soup.select('.article-paragraph')
                        if paragraphs:
                            texts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
                            content = '\n\n'.join(texts)
                        
                        # 方法2: 如果方法1失败，尝试其他常见选择器（兜底）
                        if not content:
                            selectors = [
                                '.article-body-item',      # 外层容器
                                '.article-content',
                                '[itemprop="articleBody"]',
                                'article'
                            ]
                            for sel in selectors:
                                content_elem = article_soup.select_one(sel)
                                if content_elem:
                                    for tag in content_elem.find_all(['script', 'style', 'aside', '.byline', '.author-bio']):
                                        tag.decompose()
                                    texts = [p.get_text(strip=True) for p in content_elem.find_all(['p', 'div']) if p.get_text(strip=True)]
                                    content = '\n\n'.join(texts)
                                    if content:
                                        break
                        
                        # 提取图片
                        images = []
                        for img in article_soup.select('.article-paragraph img, .article-body-item img, figure img'):
                            src = img.get('src', '')
                            if src and not any(x in src.lower() for x in ['icon', 'logo', 'author']):
                                if src.startswith('/'):
                                    src = 'https://cn.nytimes.com' + src
                                images.append({
                                    'url': src, 
                                    'alt': img.get('alt', ''), 
                                    'caption': img.get('alt', '')
                                })
                        
                        # 只检查非空，长度交给SQL存储过程判断
                        if content:
                            articles.append({
                                'title': title[:300],
                                'content': content[:20000],  # 仅截断，不判断长度
                                'source_url': href,
                                'source_name': '纽约时报-中文',
                                'published_at': pub_time,
                                'image_url': images[0]['url'] if images else None,
                                'images': images,
                                'category_hint': 'international',
                                'country_hint': 'US',
                                'fetch_method': 'html_nytimes_cn'
                            })
                            print(f"    ✓ 获取成功 ({len(content)}字)")
                        else:
                            print(f"    ✗ 内容为空")
                        
                        time.sleep(1.5)
                        
                    except Exception as e:
                        print(f"    ✗ 失败: {str(e)[:40]}")
                        continue
                
                all_articles.extend(articles)
                time.sleep(1)
                
            except Exception as e:
                print(f"[HTML] ✗ 纽约时报-中文 {url}: {str(e)[:50]}")
                continue
        
        print(f"[HTML] ✓ 纽约时报-中文: 共 {len(all_articles)} 条")
        return all_articles

    def fetch_all_html_sources(self):
        """抓取所有HTML源（包括国内和国际）"""
        all_articles = []
        
        # 国内源
        all_articles.extend(self.fetch_xinhua() or [])
        all_articles.extend(self.fetch_scmp() or [])
        all_articles.extend(self.fetch_cnn() or [])
        all_articles.extend(self.fetch_cctv() or [])
        all_articles.extend(self.fetch_aljazeera() or [])
        all_articles.extend(self.fetch_globaltimes() or [])
        
        # 国际源（替代RSS）
        all_articles.extend(self.fetch_sciencedaily() or [])
        time.sleep(1)
        all_articles.extend(self.fetch_sputnik() or [])
        time.sleep(1)
        all_articles.extend(self.fetch_nytimes_cn() or [])
        
        return all_articles
