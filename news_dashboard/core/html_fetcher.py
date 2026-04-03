import json

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil import parser as date_parser
import time
import re
import html

# 尝试导入 curl_cffi，用于绕过 Cloudflare/Akamai 等反爬
_CURL_CFFI_AVAILABLE = False
try:
    from curl_cffi import requests as curl_requests
    _CURL_CFFI_AVAILABLE = True
except ImportError:
    curl_requests = None

class HTMLNewsFetcher:
    """
    国内网站HTML直接抓取（绕过过期RSS）- 修复版
    新增：对 WSJ/Reuters 等启用 TLS 指纹伪装的 curl_cffi 会话
    """
    
    def __init__(self):
        self.session = requests.Session()
        # 国内网站需要模拟浏览器，否则可能返回403或反爬页面
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        })
    
    def _get_curl_session(self):
        """
        获取 curl_cffi Session（模拟 Chrome TLS 指纹），专门用于高反爬站点
        """
        if _CURL_CFFI_AVAILABLE and curl_requests is not None:
            return curl_requests.Session(impersonate="chrome120")
        return None
    
    def _get_soup(self, url, timeout=15, use_curl=False, curl_session=None, headers=None):
        """
        通用请求封装：支持普通 requests 和 curl_cffi
        返回 (soup, response_text) 或抛出异常
        """
        req_headers = headers or {}
        if use_curl and curl_session is not None:
            resp = curl_session.get(url, timeout=timeout, headers=req_headers)
        else:
            resp = self.session.get(url, timeout=timeout, headers=req_headers)
        resp.raise_for_status()
        # 自动推断编码
        if resp.encoding:
            resp.encoding = resp.apparent_encoding or 'utf-8'
        else:
            resp.encoding = 'utf-8'
        text = resp.text
        soup = BeautifulSoup(text, 'lxml')
        return soup, text
    
    def fetch_xinhua(self):
        """
        新华网-时政频道抓取 - 修复版：精准抓取正文区域内媒体
        策略：只抓取 detailContent / article / main 内的图片，避免导航栏杂质
        """
        url = 'http://www.xinhuanet.com/politics/'
        articles = []

        try:
            print(f"[HTML] 抓取: 新华网-时政")
            response = self.session.get(url, timeout=15)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'lxml')
            
            selectors = [
                '.news-list li',
                '.part-list li', 
                '.data-list li',
                '#news-list li',
                '.list-item',
                'h3 a[href*="/politics/"]',
                'a[href*=".news.cn/politics/"]',
                'a[href*="/2026"]'
            ]
            
            news_items = []
            for selector in selectors:
                items = soup.select(selector)
                if items:
                    news_items = items[:50]
                    break
            
            if not news_items:
                news_items = soup.find_all('a', href=re.compile(r'news\.cn/politics/\d{8}/'))[:50]

            for item in news_items:
                try:
                    if item.name == 'a':
                        a_tag = item
                    else:
                        a_tag = item.find('a', href=re.compile(r'news\.cn|xinhuanet\.com'))
                    
                    if not a_tag:
                        continue
                    
                    title = a_tag.get_text(strip=True)
                    link = a_tag.get('href', '').strip().replace(' ', '')
                    
                    if link.startswith('//'):
                        link = 'http:' + link
                    elif link.startswith('/'):
                        link = 'http://www.xinhuanet.com' + link
                    
                    if not link or not re.search(r'(\d{8})/[a-f0-9]+/c\.html$', link):
                        continue

                    pub_time = datetime.now()
                    parent = item.find_parent()
                    if parent:
                        time_meta = parent.find('meta', attrs={'timestamp': True})
                        if time_meta:
                            try:
                                pub_time = datetime.strptime(time_meta['timestamp'], '%Y-%m-%d %H:%M')
                            except:
                                pass
                    
                    date_match = re.search(r'/(\d{8})/', link)
                    if date_match and 'time_meta' not in locals():
                        try:
                            pub_time = datetime.strptime(date_match.group(1), '%Y%m%d')
                        except:
                            pass

                    print(f"  [Debug] 正在获取全文: {title[:30]}...")
                    
                    # 使用新华网专用的详情页抓取，而非通用方法
                    content, article_time, images, videos = self._fetch_xinhua_article_detail(link)
                    
                    if article_time != datetime.now():
                        pub_time = article_time

                    # 严格过滤：只保留明确在正文区域的图片（URL包含日期特征，且非二维码）
                    valid_images = []
                    for img in images:
                        img_url = img['url']
                        # 过滤二维码、图标、logo（强化规则）
                        if any(x in img_url.lower() for x in ['qrcode', 'qr_code', 'detail', 'icon', 'logo', 'share', 'wechat', 'weibo', 'ad_', 'advert']):
                            continue
                        # 确保URL完整（新华图片通常是相对路径）
                        if not img_url.startswith('http'):
                            # 基于文章URL构建图片绝对路径
                            # 文章URL格式: http://www.news.cn/20260325/xxxxx/c.html
                            # 图片URL格式: 20260325xxxxx.jpg（同目录或上级目录）
                            base_article_url = link.rsplit('/', 1)[0]  # 去掉/c.html
                            if img_url.startswith('/'):
                                # 绝对路径，补全域名
                                if 'xinhuanet.com' in link:
                                    img_url = 'http://www.xinhuanet.com' + img_url
                                else:
                                    img_url = 'http://www.news.cn' + img_url
                            else:
                                # 相对路径，基于文章目录
                                img_url = base_article_url + '/' + img_url
                        
                        img['url'] = img_url
                        valid_images.append(img)

                    # 过滤视频URL（确保是有效的mp4或m3u8）
                    valid_videos = []
                    for vid in videos:
                        vid_url = vid['url']
                        if any(x in vid_url.lower() for x in ['.mp4', '.m3u8', 'vodpub', 'news.cn']):
                            valid_videos.append(vid)

                    if content:
                        articles.append({
                            'title': title[:300],
                            'summary': content[:500],
                            'content': content[:15000],
                            'source_url': link,
                            'source_name': '新华网-时政',
                            'published_at': pub_time,
                            'image_url': valid_images[0]['url'] if valid_images else None,
                            'images': valid_images,
                            'videos': valid_videos,
                            'category_hint': 'politics',
                            'country_hint': 'CN',
                            'fetch_method': 'html_xinhua'
                        })
                        print(f"  [Debug] ✓ 成功: {title[:20]}... ({len(content)}字, {len(valid_images)}图, {len(valid_videos)}视频)")
                    else:
                        print(f"  [Debug] ✗ 内容太短: {title[:20]}")
                    
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
    
    def _fetch_xinhua_article_detail(self, url):
        """
        新华网详情页专用解析：精准定位正文区域 detailContent
        """
        try:
            response = self.session.get(url, timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'lxml')
            
            # 提取时间 - 优先meta timestamp
            pub_time = datetime.now()
            time_meta = soup.find('meta', attrs={'timestamp': True})
            if time_meta:
                try:
                    pub_time = datetime.strptime(time_meta['timestamp'], '%Y-%m-%d %H:%M')
                except:
                    pass
            else:
                time_elem = soup.find('time') or soup.select_one('.h-time, .info-source')
                if time_elem:
                    time_text = time_elem.get_text()
                    match = re.search(r'(\d{4}[-年]\d{2}[-月]\d{2}[^\d]*\d{2}:\d{2})', time_text)
                    if match:
                        try:
                            time_str = match.group(1).replace('年', '-').replace('月', '-').replace('日', ' ')
                            pub_time = datetime.strptime(time_str.strip(), '%Y-%m-%d %H:%M')
                        except:
                            pass
            
            # 提取正文 - 严格限定在 detailContent 或 articleContent
            content = ''
            content_container = None
            
            # 优先查找 detailContent（新华网标准正文容器）
            content_container = soup.select_one('#detailContent, #detail, .article-content, article')
            
            if content_container:
                # 清理脚本和样式
                for tag in content_container.find_all(['script', 'style', 'iframe', 'nav', 'header', 'footer']):
                    tag.decompose()
                
                # 提取段落
                texts = []
                for p in content_container.find_all(['p', 'div']):
                    text = p.get_text(strip=True)
                    if text and len(text) > 3:
                        texts.append(text)
                
                # 去重
                seen = set()
                unique_texts = []
                for t in texts:
                    if t not in seen and not t.endswith(('纠错', '编辑：', '责任编辑')):
                        seen.add(t)
                        unique_texts.append(t)
                content = '\n\n'.join(unique_texts)
            
            # 提取图片 - 只在正文容器内查找
            images = []
            if content_container:
                for img in content_container.find_all('img'):
                    src = img.get('src', '').strip()
                    if not src:
                        src = img.get('data-src', '').strip()
                    
                    if src:
                        # 过滤明显的非正文图片（根据文件名特征）
                        if any(x in src.lower() for x in ['qrcode', 'qr_', 'icon', 'logo', 'share', 'weibo', 'wechat']):
                            continue
                        images.append({
                            'url': src,
                            'alt': img.get('alt', ''),
                            'caption': img.get('title', '')
                        })
            
            # 提取视频 - 查找 detailContent 内的 video 标签 或特定播放器div
            videos = []
            if content_container:
                # 方法1: 直接查找video标签
                for video in content_container.find_all('video'):
                    src = video.get('src', '').strip()
                    if src:
                        videos.append({
                            'url': src,
                            'type': 'direct',
                            'platform': 'xinhua'
                        })
                    # 查找source子标签
                    for source in video.find_all('source'):
                        src = source.get('src', '').strip()
                        if src:
                            videos.append({
                                'url': src,
                                'type': 'source',
                                'platform': 'xinhua'
                            })
                
                # 方法2: 查找新华网特定播放器（如DH-PLAYER）
                for player_div in content_container.find_all('div', id=re.compile(r'DH-PLAYER|player')):
                    video = player_div.find('video')
                    if video:
                        src = video.get('src', '').strip()
                        if src and src not in [v['url'] for v in videos]:
                            videos.append({
                                'url': src,
                                'type': 'player',
                                'platform': 'xinhua'
                            })
            
            return content, pub_time, images, videos
            
        except Exception as e:
            print(f"    [Error] 新华网详情页失败: {e}")
            return '', datetime.now(), [], []

    def _fetch_article_content(self, url):
        """
        通用详情页抓取（用于非新华网站点）
        """
        try:
            response = self.session.get(url, timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'lxml')

            pub_time = datetime.now()
            time_selectors = [
                '.head-line span', '.info-source', 'span[data-time]',
                '.post-time', 'time', '[id*="time"]', '[class*="date"]',
                '.article__info-date', '.byline time', '[timestamp]'
            ]

            for selector in time_selectors:
                elements = soup.select(selector)
                for element in elements:
                    if element.get('timestamp'):
                        try:
                            pub_time = datetime.strptime(element['timestamp'], '%Y-%m-%d %H:%M')
                            break
                        except:
                            pass
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

            content_selectors = [
                'article', 'main',
                'div[id*="content"]', 'div[id*="article"]', 'div[id*="story"]',
                'div[class*="content"]', 'div[class*="article"]', 'div[class*="story"]',
                'div[class*="body"]', 'div[class*="text"]', 'div[class*="post"]',
                'div.main', '#p-detail', '.main-content', '#article-content',
                '.content-detail', 'div.article__body', 'div.l-container', 
                'section#body-text', 'div.zn-body__paragraph', 'div.Article__content',
                '#story_text', '.article_content', '.article__body',
                '.article-paragraph', '.article-body-item'
            ]

            content = ''
            content_container = None
            
            for selector in content_selectors:
                try:
                    content_div = soup.select_one(selector)
                    if content_div:
                        content_container = content_div
                        for tag in content_div.find_all(['script', 'style', 'iframe', 'aside', 'nav', 'header', 'footer']):
                            tag.decompose()

                        texts = []
                        for elem in content_div.find_all(['p', 'div', 'h2', 'h3', 'h4', 'h5', 'li']):
                            text = elem.get_text(strip=True)
                            if text and len(text) > 3 and not text.endswith((':','：','；', ';')):
                                texts.append(text)
                        
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
            
            if not content or len(content) < 200:
                texts = []
                for p in soup.find_all('p'):
                    text = p.get_text(strip=True)
                    if text and len(text) > 5:
                        texts.append(text)
                if texts:
                    content = '\n\n'.join(texts)

            # 媒体提取（只在正文容器内）
            images = []
            videos = []
            base_url = '/'.join(url.split('/')[:3])
            
            is_aljazeera = 'aljazeera.com' in url
            is_sciencedaily = 'sciencedaily.com' in url
            is_globaltimes = 'globaltimes.cn' in url
            is_sputnik = 'sputniknews.cn' in url
            is_nytimes_cn = 'cn.nytimes.com' in url

            if content_container:
                for img in content_container.find_all('img'):
                    src = img.get('src', '').strip()
                    if not src:
                        src = img.get('data-src', '').strip() or img.get('data-original', '').strip()
                    
                    if not src:
                        continue
                    
                    skip_patterns = ['qrcode', 'qr-code', 'detail', 'icon', 'logo', 'avatar', 
                                   'button', 'share', 'wechat', 'weibo', 'facebook', 'twitter',
                                   'svg', 'gif', 'advertisement', 'ad-', '_ad_', 'tracking',
                                   'pixel', 'spacer', 'blank', 'placeholder', 'loading', 'loading-icon']
                    
                    if any(pattern in src.lower() for pattern in skip_patterns):
                        continue
                    
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = base_url + src
                    elif not src.startswith('http'):
                        if url.endswith('/'):
                            src = url + src
                        else:
                            src = url.rsplit('/', 1)[0] + '/' + src
                    
                    if is_aljazeera and not src.startswith('http'):
                        src = 'https://www.aljazeera.com' + src
                    elif is_sciencedaily and not src.startswith('http'):
                        src = 'https://www.sciencedaily.com' + src
                    elif is_globaltimes and not src.startswith('http'):
                        src = 'https://www.globaltimes.cn' + src
                    elif is_sputnik and src.startswith('//'):
                        src = 'https:' + src
                    elif is_nytimes_cn and src.startswith('//'):
                        src = 'https:' + src
                    
                    alt = img.get('alt', '').strip()
                    title = img.get('title', '').strip()
                    caption = ''
                    parent = img.find_parent(['figure', 'div', 'p'])
                    if parent:
                        figcaption = parent.find('figcaption')
                        if figcaption:
                            caption = figcaption.get_text(strip=True)
                    
                    images.append({
                        'url': src,
                        'alt': alt or title or '',
                        'caption': caption or alt or title or ''
                    })

                for video_tag in content_container.find_all('video'):
                    src = video_tag.get('src', '').strip()
                    if src:
                        if src.startswith('//'):
                            src = 'https:' + src
                        elif src.startswith('/'):
                            src = base_url + src
                        videos.append({
                            'url': src,
                            'type': 'direct',
                            'platform': 'unknown'
                        })
                    
                    for source in video_tag.find_all('source'):
                        src = source.get('src', '').strip()
                        if src:
                            if src.startswith('//'):
                                src = 'https:' + src
                            elif src.startswith('/'):
                                src = base_url + src
                            if not any(v['url'] == src for v in videos):
                                videos.append({
                                    'url': src,
                                    'type': 'source',
                                    'platform': 'unknown'
                                })

                for iframe in content_container.find_all('iframe'):
                    src = iframe.get('src', '').strip()
                    if not src:
                        continue
                    
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = base_url + src
                    
                    platform = 'unknown'
                    if any(x in src for x in ['youtube.com', 'youtu.be']):
                        platform = 'youtube'
                    elif 'vimeo.com' in src:
                        platform = 'vimeo'
                    elif 'bilibili.com' in src:
                        platform = 'bilibili'
                    elif 'player.aljazeera.com' in src or 'aljazeera.com' in src:
                        platform = 'aljazeera'
                    elif 'nytimes.com' in src:
                        platform = 'nytimes'
                    
                    videos.append({
                        'url': src,
                        'type': 'iframe',
                        'platform': platform
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


    def fetch_cnn(self):
        """CNN世界新闻抓取 - 修复版：区分视频页/文章页，过滤无用图片"""
        url = 'https://edition.cnn.com/world'
        print(f"[HTML] 抓取: CNN-World")
        try:
            response = self.session.get(url, timeout=20)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'lxml')

            # 收集链接但过滤掉复杂页面（live-news等）
            candidate = self._gather_article_links(
                soup,
                selectors=['.cd__headline a', 'h3 a', 'a[href*="/2026/"]'],
                base_url='https://edition.cnn.com',
                href_regex=r'https?://edition\.cnn\.com/.+',
                limit=80
            )

            articles = []
            for link in candidate:
                # 过滤掉实时新闻等复杂页面
                if '/live-news/' in link or '/live/' in link:
                    print(f"  [Debug] CNN 跳过复杂页面: {link}")
                    continue
            
                try:
                    print(f"  [Debug] CNN 获取: {link}")
                    # 使用CNN专用解析方法
                    content, pub_time, images, videos = self._fetch_cnn_article_detail(link)
                
                    if content:
                        # 提取标题（从URL或页面）
                        title = ''
                        if '/video/' in link:
                            # 视频页优先使用视频标题（在详情页方法中已提取）
                            title = videos[0].get('title', '') if videos else ''
                        if not title:
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
                            'fetch_method': 'html_cnn_v2'
                        })
                        print(f"  [Debug] CNN ✓ 成功: {link} ({len(content)}字, {len(images)}图, {len(videos)}视频)")
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

    def _fetch_cnn_article_detail(self, url):
        """
        CNN详情页专用解析：区分视频页和文章页，严格过滤图片
        """
        try:
            response = self.session.get(url, timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'lxml')
        
            # 判断页面类型
            is_video_page = '/video/' in url or bool(soup.find('div', {'data-component-name': 'video-resource'}))
        
            if not is_video_page:
                return self._fetch_cnn_article_page(soup, url)
            
        except Exception as e:
            print(f"    [Error] CNN详情页失败: {e}")
            return '', datetime.now(), [], []

    def _fetch_cnn_article_page(self, soup, url):
        """CNN文章页解析：提取正文、严格过滤内容图片"""
        content = ''
        images = []
        videos = []
        pub_time = datetime.now()
    
        # 提取时间 - CNN文章页通常在time标签或data-publish-date
        time_elem = soup.find('time') or soup.find('div', {'data-publish-date': True})
        if time_elem:
            datetime_val = time_elem.get('datetime') or time_elem.get('data-publish-date', '')
            if datetime_val:
                try:
                    pub_time = datetime.strptime(datetime_val[:19], '%Y-%m-%dT%H:%M:%S')
                except:
                    try:
                        pub_time = datetime.strptime(datetime_val, '%Y-%m-%d %H:%M')
                    except:
                        pass
    
        # 提取正文 - CNN文章在article__content容器内
        content_container = soup.find('div', {'class': 'article__content'}) or \
                           soup.find('main', {'class': 'article__main'}) or \
                           soup.find('article')
    
        if content_container:
            # 清理脚本和样式
            for tag in content_container.find_all(['script', 'style', 'iframe', 'nav', 'aside']):
                tag.decompose()
        
            # 提取段落（优先使用paragraph-elevate类，这是CNN文章段落的特定类）
            paragraphs = content_container.find_all(['p', 'div'], class_=['paragraph-elevate', 'vossi-paragraph_elevate'])
        
            if not paragraphs:
                # 备用方案：查找所有文本段落
                paragraphs = content_container.find_all(['p', 'h2', 'h3'])
        
            texts = []
            for p in paragraphs:
                text = p.get_text(strip=True)
                # 过滤广告和导航文本
                if text and len(text) > 20 and not any(x in text.lower() for x in ['advertisement', 'ad feedback', 'cnn sans']):
                    texts.append(text)
        
            content = '\n\n'.join(texts)
    
        # 提取图片 - 严格限制：只保留 media.cnn.com/api/v1/images/stellar/prod/ 路径的图片
        if content_container:
            for img in content_container.find_all('img'):
                src = img.get('src', '').strip()
                if not src:
                    src = img.get('data-src', '').strip() or img.get('data-url', '').strip()
            
                if not src:
                    continue
            
                # CNN规则：只保留 media.cnn.com 的 stellar/prod 路径图片（内容图片）
                # 排除：图标、logo、社交按钮、广告等
                if 'media.cnn.com/api/v1/images/stellar/prod/' not in src:
                    continue
            
                # 额外过滤：排除明显的小图标（通过URL特征）
                if any(x in src.lower() for x in ['icon', 'logo', 'avatar', 'social', 'share', 'button']):
                    continue
            
                # 获取图片说明
                alt = img.get('alt', '').strip()
                caption = ''
            
                # 尝试从父元素获取说明（figcaption或inline-placeholder）
                parent = img.find_parent(['figure', 'div', 'span'])
                if parent:
                    caption_elem = parent.find('figcaption') or parent.find('span', {'data-editable': 'metaCaption'})
                    if caption_elem:
                        caption = caption_elem.get_text(strip=True)
            
                images.append({
                    'url': src,
                    'alt': alt,
                    'caption': caption or alt
                })
        
            # 去重
            seen_urls = set()
            unique_images = []
            for img in images:
                if img['url'] not in seen_urls:
                    seen_urls.add(img['url'])
                    unique_images.append(img)
            images = unique_images
    
        # 提取视频（文章内嵌视频）
        for iframe in content_container.find_all('iframe') if content_container else []:
            src = iframe.get('src', '').strip()
            if src and ('cnn.com' in src or 'turner.com' in src):
                videos.append({
                    'url': src,
                    'type': 'iframe',
                    'platform': 'cnn'
                })
    
        return content, pub_time, images, videos

    def fetch_jiemian(self):
        """
        界面新闻HTML抓取 - 使用requests直接抓取（无需浏览器）
        URL: https://www.jiemian.com/lists/4.html
        注意：界面新闻是服务端渲染，可直接用requests
        """
        url = 'https://www.jiemian.com/lists/4.html'
        print("[HTML] 抓取: 界面新闻")
        
        try:
            articles = []
            
            # 获取列表页
            response = self.session.get(url, timeout=15)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'lxml')
            
            # 提取新闻链接 - 界面新闻使用 /article/ 格式
            links = soup.find_all('a', href=re.compile(r'/article/\d+'))
            print(f"  [Debug] 找到 {len(links)} 个链接")
            
            # 去重处理
            seen_urls = set()
            unique_links = []
            for a in links:
                href = a['href']
                if not href.startswith('http'):
                    href = 'https://www.jiemian.com' + href
                
                title = a.get_text(strip=True)
                if title and len(title) > 5 and href not in seen_urls:
                    seen_urls.add(href)
                    unique_links.append((title, href))
            
            print(f"  [Debug] 去重后: {len(unique_links)} 个")
            
            # 抓取详情页
            for title, href in unique_links[:15]:
                try:
                    content, pub_time, images, videos = self._fetch_jiemian_article(href)
                    
                    if content and len(content) > 30:
                        articles.append({
                            'title': title[:300],
                            'summary': content[:500],
                            'content': content[:15000],
                            'source_url': href,
                            'source_name': '界面新闻',
                            'published_at': pub_time,
                            'image_url': images[0]['url'] if images else None,
                            'images': images,
                            'videos': videos,
                            'category_hint': 'finance',
                            'country_hint': 'CN',
                            'fetch_method': 'requests_jiemian'
                        })
                        video_info = f", {len(videos)}视频" if videos else ", 无视频"
                        print(f"    [OK] {title[:30]}... ({len(content)}字, {len(images)}图{video_info})")
                    else:
                        print(f"    [SKIP] 内容太短: {title[:30]}...")
                    
                    time.sleep(0.3)
                except Exception as e:
                    print(f"    [ERR] 失败: {str(e)[:50]}")
                    continue
            
            print(f"[HTML] [OK] 界面新闻: {len(articles)} 条")
            return articles
            
        except Exception as e:
            print(f"[HTML] [ERR] 界面新闻: {e}")
            return []
    
    def _fetch_jiemian_article(self, url):
        """
        抓取界面新闻详情页
        """
        resp = self.session.get(url, timeout=10)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'lxml')
        
        # 标题 - 优先从页面获取
        h1 = soup.find('h1', class_='article-title') or soup.find('h1')
        title = h1.get_text(strip=True) if h1 else ''
        
        # 时间
        pub_time = datetime.now()
        time_elem = soup.find('span', class_='article-time') or soup.find('time')
        if time_elem:
            time_text = time_elem.get_text(strip=True)
            try:
                # 界面新闻时间格式: 2025-03-30 18:30
                pub_time = datetime.strptime(time_text, '%Y-%m-%d %H:%M')
            except:
                try:
                    pub_time = date_parser.parse(time_text)
                except:
                    pass
        
        # 正文内容
        content = ''
        content_div = soup.find('div', class_='article-content') or soup.find('article')
        
        if content_div:
            # 清理script和style
            for tag in content_div.find_all(['script', 'style', 'iframe']):
                tag.decompose()
            
            # 提取段落
            texts = []
            for p in content_div.find_all('p'):
                text = p.get_text(strip=True)
                if text and len(text) > 3:
                    texts.append(text)
            content = '\n\n'.join(texts)
        
        # 提取图片 - 界面新闻图片可能有懒加载(data-src)
        images = []
        if content_div:
            for img in content_div.find_all('img'):
                src = img.get('data-src') or img.get('src')
                if src and not src.startswith('data:'):
                    # 补全URL
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = 'https://www.jiemian.com' + src
                    images.append({
                        'url': src,
                        'alt': img.get('alt', title),
                        'caption': img.get('alt', title)
                    })
        
        # 提取视频
        videos = []
        if content_div:
            # 查找video标签
            for video in content_div.find_all('video'):
                src = video.get('src')
                if src:
                    videos.append({'url': src, 'type': 'mp4'})
            
            # 查找iframe视频（腾讯视频、优酷等）
            for iframe in content_div.find_all('iframe'):
                src = iframe.get('src')
                if src and ('video' in src or 'player' in src):
                    videos.append({
                        'url': src,
                        'type': 'iframe',
                        'platform': 'external'
                    })
            
            # 从script中查找视频链接
            scripts = content_div.find_all('script')
            for script in scripts:
                if script.string:
                    # 查找mp4或m3u8链接
                    video_urls = re.findall(r'https?://[^\s"\'<>]+\.(?:mp4|m3u8)', script.string)
                    for vurl in video_urls:
                        if vurl not in [v['url'] for v in videos]:
                            videos.append({'url': vurl, 'type': 'video'})
        
        return content, pub_time, images, videos

    def fetch_aljazeera(self):
        """
        Al Jazeera 英文新闻爬取 - 修复版
        URL: https://www.aljazeera.com/
        """
        articles = []
        categories = ['news', 'americas', 'asia', 'middle-east']
        
        try:
            for category in categories:
                url = f'https://www.aljazeera.com/{category}/'
                print(f"[HTML] 抓取: Al Jazeera-{category}")
                
                try:
                    response = self.session.get(url, timeout=15)
                    response.encoding = 'utf-8'
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 修复选择器，扩大范围
                    article_links = soup.find_all('a', href=re.compile(r'/news/\d{4}/\d{2}/\d{2}/'))
                    
                    if not article_links:
                        article_links = soup.select('article a[href*="/news/"], .article-card a, .top-article a, h2 a[href*="/news/"]')
                    
                    processed_urls = set()
                    
                    for link in article_links[:15]:
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
                            content, pub_time, images, videos = self._fetch_article_content(href)
                            
                            # Al Jazeera图片URL修复（通常是相对路径）
                            for img in images:
                                if not img['url'].startswith('http'):
                                    img['url'] = 'https://www.aljazeera.com' + img['url']
                            
                            if content and len(content) > 100:
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
                                print(f"  [Debug] ✓ 成功 ({len(content)}字, {len(images)}图, {len(videos)}视频)")
                            else:
                                print(f"  [Debug] ✗ 内容不足")
                            
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

    def fetch_globaltimes(self):
        """
        环球时报中文新闻爬取 - 修复版
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
                        article_links = soup.select('.article_list a[href*="/page/"], .new_title_s a')
                    
                    processed_urls = set()
                    
                    for link in article_links[:15]:
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
                                print(f"  [Debug] ✓ 成功 ({len(content)}字, {len(images)}图, {len(videos)}视频)")
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
        """获取环球时报文章详情页 - 修复图片抓取"""
        try:
            response = self.session.get(url, timeout=15)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            pub_time = datetime.now()
            # 查找时间元素
            for elem in soup.select('.pub_time, .author_share_left span[class*="time"], [class*="date"]'):
                text = elem.get_text(strip=True)
                match = re.search(r'(\d{4}[年/-]\d{2}[月/-]\d{2}[日]?)\s*(\d{2}:\d{2})?', text)
                if match:
                    try:
                        time_str = match.group(1).replace('年', '-').replace('月', '-').replace('日', '')
                        if match.group(2):
                            time_str += ' ' + match.group(2)
                        pub_time = date_parser.parse(time_str)
                        break
                    except:
                        pass
            
            # 提取正文
            content = ''
            content_selectors = [
                '.article_content',
                '.article_right',
                'div[class*="article-content"]',
                'div[class*="article_body"]',
                'article'
            ]
            
            for selector in content_selectors:
                content_div = soup.select_one(selector)
                if content_div:
                    for tag in content_div.find_all(['script', 'style', 'iframe']):
                        tag.decompose()
                    
                    texts = []
                    for p in content_div.find_all(['p', 'div']):
                        text = p.get_text(strip=True)
                        if text and len(text) > 10:
                            texts.append(text)
                    
                    if texts:
                        content = '\n\n'.join(texts)
                        break
            
            if not content:
                body = soup.find('div', class_='article')
                if body:
                    content = body.get_text('\n', strip=True)
            
            # 提取图片 - 环球时报图片通常在 article_content 中的 img 标签，可能使用 data-src
            images = []
            for img in soup.select('.article_content img, .article_right img, center img'):
                src = img.get('src', '').strip()
                if not src:
                    # 尝试从data-src获取（懒加载）
                    src = img.get('data-src', '').strip()
                
                if src:
                    # 补全URL
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = 'https://www.globaltimes.cn' + src
                    elif not src.startswith('http'):
                        src = 'https://www.globaltimes.cn/' + src
                    
                    # 过滤无效图片
                    if any(x in src.lower() for x in ['icon', 'logo', 'qrcode', 'share', 'button']):
                        continue
                    
                    alt = img.get('alt', '').strip()
                    caption = ''
                    # 尝试获取图片说明（通常在center标签后的p.picture）
                    parent = img.find_parent('center')
                    if parent:
                        next_p = parent.find_next_sibling('p')
                        if next_p and 'picture' in str(next_p.get('class', [])):
                            caption = next_p.get_text(strip=True)
                    
                    images.append({
                        'url': src,
                        'alt': alt,
                        'caption': caption or alt
                    })
            
            # 提取视频
            videos = []
            for iframe in soup.find_all('iframe'):
                src = iframe.get('src', '')
                if src and any(x in src for x in ['youtube', 'youku', 'video']):
                    if src.startswith('//'):
                        src = 'https:' + src
                    videos.append({
                        'url': src,
                        'type': 'iframe',
                        'platform': 'unknown'
                    })
            
            return content, pub_time, images, videos
        
        except Exception as e:
            print(f"    [Error] 获取环球时报文章失败: {e}")
            return '', datetime.now(), [], []

    def fetch_sciencedaily(self):
        """
        ScienceDaily HTML抓取 - 修复版（修复图片URL）
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
                    date_elem = article_soup.find('dt', string='Date:')
                    if date_elem:
                        date_text = date_elem.find_next('dd').get_text(strip=True) if date_elem.find_next('dd') else ''
                        if date_text:
                            try:
                                pub_time = date_parser.parse(date_text)
                            except:
                                pass
                    
                    # 提取正文 - 保持原有逻辑不变
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
                    
                    # 修复图片提取 - 扩展选择器以覆盖 #story_text, #featured, figure等
                    images = []
                    # 关键修复：使用更广泛的选择器覆盖外层容器 #story_text 和特色图片区 #featured
                    img_selectors = [
                        '#story_text img',      # 外层故事容器（包含#featured和#text）
                        '#featured img',        # 顶部特色图片区
                        'figure img',           # 所有figure标签内的图片
                        '.mainimg img',         # 主图片类
                        '#text img',            # 正文区图片（原有）
                        '.lead img', 
                        '[itemprop="articleBody"] img', 
                        '.main-content img'
                    ]
                    
                    processed_imgs = set()  # 防止重复
                    
                    for selector in img_selectors:
                        for img in article_soup.select(selector):
                            src = img.get('src', '').strip()
                            
                            # 如果没有src但有srcset，从srcset提取第一个URL（通常是高分辨率版本）
                            if not src:
                                srcset = img.get('srcset', '').strip()
                                if srcset:
                                    # srcset格式: "url1 600w, url2 1200w..."，取第一个URL
                                    src = srcset.split(',')[0].split()[0]
                            
                            if not src or src in processed_imgs:
                                continue
                            
                            # 排除图标类图片（保留.gif排除逻辑）
                            if src.endswith('.gif') or any(x in src.lower() for x in ['icon', 'logo', 'button']):
                                continue
                            
                            # 补全URL（关键修复：处理 /images/... 相对路径）
                            if src.startswith('/'):
                                src = 'https://www.sciencedaily.com' + src
                            elif not src.startswith('http'):
                                src = 'https://www.sciencedaily.com/' + src
                            
                            processed_imgs.add(src)
                            
                            alt = img.get('alt', '')
                            # 尝试获取figcaption作为caption
                            caption = ''
                            figure_parent = img.find_parent('figure')
                            if figure_parent:
                                figcaption = figure_parent.find('figcaption')
                                if figcaption:
                                    caption = figcaption.get_text(strip=True)
                            if not caption:
                                caption = img.get('title', alt)
                                
                            images.append({
                                'url': src, 
                                'alt': alt, 
                                'caption': caption
                            })
                    
                    # 视频提取（保持原有逻辑）
                    videos = []
                    for iframe in article_soup.find_all('iframe'):
                        src = iframe.get('src', '')
                        if src:
                            if src.startswith('//'):
                                src = 'https:' + src
                            elif src.startswith('/'):
                                src = 'https://www.sciencedaily.com' + src
                            videos.append({
                                'url': src,
                                'type': 'iframe',
                                'platform': 'unknown'
                            })

                    if content and len(content) > 200:
                        articles.append({
                            'title': title[:300],
                            'content': content[:20000],
                            'source_url': link,
                            'source_name': 'ScienceDaily',
                            'published_at': pub_time,
                            'image_url': images[0]['url'] if images else None,
                            'images': images,
                            'videos': videos,
                            'category_hint': 'science',
                            'country_hint': 'US',
                            'fetch_method': 'html_sciencedaily'
                        })
                        print(f"    ✓ {len(content)} 字, {len(images)} 图, {len(videos)} 视频")
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

    def fetch_sputnik(self):
        """
        俄罗斯卫星通讯社 HTML抓取 - 修复版（整合内嵌详情页抓取）
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
                
                for title, href in unique_links:
                    try:
                        print(f"  [Sputnik] 获取: {title[:50]}...")
                        
                        # 内嵌详情页抓取逻辑（避免调用_fetch_article_content以确保结构正确）
                        article_resp = session.get(href, timeout=10)
                        article_resp.encoding = 'utf-8'
                        article_soup = BeautifulSoup(article_resp.text, 'lxml')
                        
                        # 提取时间
                        pub_time = datetime.now()
                        # 优先从meta标签提取
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
                        
                        # 提取图片 - Sputnik使用 CDN 绝对路径，但需确保抓全
                        images = []
                        # 从article__body内查找所有img（排除分享按钮等小图标）
                        for img in article_soup.select('.article__body img, .b-article__text img'):
                            src = img.get('src', '').strip()
                            if not src:
                                continue
                            
                            # 处理协议相对URL
                            if src.startswith('//'):
                                src = 'https:' + src
                            
                            # 过滤掉图标和按钮图片
                            if any(x in src.lower() for x in ['icon', 'logo', 'avatar', 'button', 'share', 'more', 'svg']):
                                continue
                            
                            alt = img.get('alt', '').strip()
                            title_img = img.get('title', '').strip()
                            
                            # 避免重复
                            if not any(i['url'] == src for i in images):
                                images.append({
                                    'url': src,
                                    'alt': alt,
                                    'caption': title_img or alt
                                })
                        
                        # 提取视频
                        videos = []
                        # 查找iframe嵌入
                        for iframe in article_soup.find_all('iframe'):
                            src = iframe.get('src', '').strip()
                            if src:
                                if src.startswith('//'):
                                    src = 'https:' + src
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
                            all_articles.append({
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
                
                time.sleep(1)
                
            except Exception as e:
                print(f"[HTML] ✗ 俄罗斯卫星通讯社 {url}: {str(e)[:50]}")
                continue
        
        print(f"[HTML] ✓ 俄罗斯卫星通讯社: 共 {len(all_articles)} 条")
        return all_articles

    def fetch_nytimes_cn(self):
        """
        纽约时报-中文 HTML抓取 - 修正版（修复图片和视频抓取）
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
                        
                        # 提取正文 - 使用 .article-paragraph 类
                        content = ''
                        
                        # 方法1: 使用 .article-paragraph 类
                        paragraphs = article_soup.select('.article-paragraph')
                        if paragraphs:
                            texts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
                            content = '\n\n'.join(texts)
                        
                        # 方法2: 兜底
                        if not content:
                            selectors = [
                                '.article-body-item',
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
                        
                        # 提取图片 - NYTimes使用 static01.nyt.com 绝对路径，但需确保协议正确
                        images = []
                        for img in article_soup.select('.article-paragraph img, .article-body-item img, figure img, .article-span-photo img'):
                            src = img.get('src', '')
                            # 尝试获取高清版本（替换 thumbLarge 为 master1050）
                            if 'thumbLarge' in src:
                                src = src.replace('thumbLarge', 'master1050')
                            
                            if src and not any(x in src.lower() for x in ['icon', 'logo', 'author']):
                                # NYTimes已经是绝对路径，但确保协议正确（处理 //static01.nyt.com）
                                if src.startswith('//'):
                                    src = 'https:' + src
                                images.append({
                                    'url': src,
                                    'alt': img.get('alt', ''),
                                    'caption': ''
                                })
                        
                        # 提取视频 - 关键修复：过滤Google Tag Manager、广告和分析iframe
                        videos = []
                        
                        # 定义需要排除的垃圾域名/模式（跟踪、广告、分析工具）
                        skip_iframe_patterns = [
                            'googletagmanager.com',      # Google Tag Manager
                            'google-analytics.com',      # Google Analytics
                            'doubleclick.net',           # Google广告
                            'googleadservices.com',      # Google广告服务
                            'facebook.com/tr/',          # Facebook跟踪像素
                            'connect.facebook.net',      # Facebook SDK
                            'bat.bing.com',              # Bing跟踪
                            'tags.tiqcdn.com',           # Tealium标签管理
                            'analytics',                 # 通用分析关键词
                            'tracker',                   # 通用跟踪关键词
                            'pixel',                     # 通用像素关键词
                            'gtm-',                      # GTM容器ID模式
                            'gtag',                      # Google标签
                            'scribe.',                   # 日志/记录服务
                            'heatmap',                   # 热力图跟踪
                            'optimizely',                # A/B测试
                            'hotjar',                    # 用户行为分析
                        ]
                        
                        for iframe in article_soup.find_all('iframe'):
                            src = iframe.get('src', '').strip()
                            if not src:
                                continue
                            
                            # 关键修复：检查并过滤掉跟踪/广告 iframe
                            src_lower = src.lower()
                            if any(pattern in src_lower for pattern in skip_iframe_patterns):
                                continue
                            
                            # 处理协议相对URL
                            if src.startswith('//'):
                                src = 'https:' + src
                            elif src.startswith('/'):
                                src = 'https://cn.nytimes.com' + src
                            
                            # 识别视频平台
                            platform = 'unknown'
                            if any(x in src for x in ['youtube.com', 'youtu.be']):
                                platform = 'youtube'
                            elif 'vimeo.com' in src:
                                platform = 'vimeo'
                            elif 'cn.nytimes.com' in src or 'nytimes.com/video' in src:
                                platform = 'nytimes'
                            elif 'player' in src:
                                platform = 'player'
                            
                            videos.append({
                                'url': src,
                                'type': 'iframe',
                                'platform': platform
                            })
                        
                        if content:
                            articles.append({
                                'title': title[:300],
                                'content': content[:20000],
                                'source_url': href,
                                'source_name': '纽约时报-中文',
                                'published_at': pub_time,
                                'image_url': images[0]['url'] if images else None,
                                'images': images,
                                'videos': videos,
                                'category_hint': 'international',
                                'country_hint': 'US',
                                'fetch_method': 'html_nytimes_cn'
                            })
                            print(f"    ✓ 获取成功 ({len(content)}字, {len(images)}图, {len(videos)}视频)")
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

    def fetch_bbc(self):
        """
        BBC 新闻 HTML抓取
        网址: https://www.bbc.com/news
        文章URL模式: https://www.bbc.com/news/articles/xxxxxxxxxx
        """
        urls = [
            'https://www.bbc.com/news',
            'https://www.bbc.com/news/world',
            'https://www.bbc.com/news/business',
            'https://www.bbc.com/news/technology',
        ]
        
        all_articles = []
        
        for url in urls:
            try:
                category = url.split('/')[-1] if url != 'https://www.bbc.com/news' else 'news'
                print(f"[HTML] 抓取: BBC-{category}")
                
                response = self.session.get(url, timeout=15, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                response.raise_for_status()
                response.encoding = 'utf-8'
                
                soup = BeautifulSoup(response.text, 'lxml')
                
                # BBC文章链接模式
                article_links = []
                for a in soup.find_all('a', href=re.compile(r'/news/articles/[a-z0-9]+')):
                    title = a.get_text(strip=True)
                    href = a.get('href', '')
                    if title and len(title) > 10:
                        if href.startswith('/'):
                            href = 'https://www.bbc.com' + href
                        article_links.append((title, href))
                
                # 去重
                seen = set()
                unique_links = []
                for title, href in article_links[:15]:
                    if href not in seen:
                        seen.add(href)
                        unique_links.append((title, href))
                
                print(f"  [Debug] {category} 找到 {len(unique_links)} 条")
                
                for title, href in unique_links:
                    try:
                        print(f"  [BBC] 获取: {title[:50]}...")
                        
                        article_resp = self.session.get(href, timeout=10, headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        })
                        article_resp.encoding = 'utf-8'
                        article_soup = BeautifulSoup(article_resp.text, 'lxml')
                        
                        # 提取时间
                        pub_time = datetime.now()
                        time_elem = article_soup.find('time') or article_soup.find('span', {'data-testid': 'timestamp'})
                        if time_elem:
                            datetime_attr = time_elem.get('datetime') or time_elem.get_text()
                            if datetime_attr:
                                try:
                                    pub_time = date_parser.parse(datetime_attr)
                                except:
                                    pass
                        
                        # 提取正文 - BBC使用 data-component="text-block"
                        content = ''
                        text_blocks = article_soup.find_all('div', {'data-component': 'text-block'})
                        if text_blocks:
                            texts = []
                            for block in text_blocks:
                                text = block.get_text(strip=True)
                                if text and len(text) > 10:
                                    texts.append(text)
                            content = '\n\n'.join(texts)
                        
                        # 兜底方案
                        if not content:
                            selectors = ['article', '[data-testid="article-body"]', '.ssrcss-pv1rh6-ArticleWrapper']
                            for sel in selectors:
                                content_elem = article_soup.select_one(sel)
                                if content_elem:
                                    for tag in content_elem.find_all(['script', 'style']):
                                        tag.decompose()
                                    texts = [p.get_text(strip=True) for p in content_elem.find_all('p') if p.get_text(strip=True)]
                                    content = '\n\n'.join(texts)
                                    if content:
                                        break
                        
                        # 提取图片 - BBC图片在 figure 标签内
                        images = []
                        for figure in article_soup.find_all('figure'):
                            img = figure.find('img')
                            if img:
                                src = img.get('src', '')
                                if not src:
                                    src = img.get('data-src', '')
                                
                                if src:
                                    if src.startswith('//'):
                                        src = 'https:' + src
                                    
                                    # 过滤小图标
                                    if any(x in src.lower() for x in ['icon', 'logo', 'avatar']):
                                        continue
                                    
                                    caption = ''
                                    caption_elem = figure.find('figcaption')
                                    if caption_elem:
                                        caption = caption_elem.get_text(strip=True)
                                    
                                    images.append({
                                        'url': src,
                                        'alt': img.get('alt', ''),
                                        'caption': caption
                                    })
                        
                        # 提取视频
                        videos = []
                        # BBC视频通常在特定div中
                        for video_div in article_soup.find_all('div', {'data-component': 'video-block'}):
                            iframe = video_div.find('iframe')
                            if iframe:
                                src = iframe.get('src', '')
                                if src:
                                    if src.startswith('//'):
                                        src = 'https:' + src
                                    videos.append({
                                        'url': src,
                                        'type': 'iframe',
                                        'platform': 'bbc'
                                    })
                        
                        if content and len(content) > 100:
                            all_articles.append({
                                'title': title[:300],
                                'content': content[:20000],
                                'source_url': href,
                                'source_name': 'BBC',
                                'published_at': pub_time,
                                'image_url': images[0]['url'] if images else None,
                                'images': images,
                                'videos': videos,
                                'category_hint': category,
                                'country_hint': 'GB',
                                'fetch_method': 'html_bbc'
                            })
                            print(f"    ✓ 获取成功 ({len(content)}字, {len(images)}图, {len(videos)}视频)")
                        else:
                            print(f"    ✗ 内容为空")
                        
                        time.sleep(1)
                        
                    except Exception as e:
                        print(f"    ✗ 失败: {str(e)[:50]}")
                        continue
                
                time.sleep(1)
                
            except Exception as e:
                print(f"[HTML] ✗ BBC {url}: {str(e)[:50]}")
                continue
        
        print(f"[HTML] ✓ BBC: 共 {len(all_articles)} 条")
        return all_articles



    def fetch_all_html_sources(self):
        """抓取所有HTML源（包括国内和国际）"""
        all_articles = []
        # 国内源
        time.sleep(1)
        all_articles.extend(self.fetch_jiemian() or [])
        all_articles.extend(self.fetch_xinhua() or [])
        all_articles.extend(self.fetch_cnn() or [])
        all_articles.extend(self.fetch_globaltimes() or [])
        
        # 国际源
        all_articles.extend(self.fetch_bbc() or [])
        time.sleep(1)
        all_articles.extend(self.fetch_sciencedaily() or [])
        time.sleep(1)
        all_articles.extend(self.fetch_sputnik() or [])
        time.sleep(1)
        all_articles.extend(self.fetch_nytimes_cn() or [])
        time.sleep(1)
        all_articles.extend(self.fetch_aljazeera() or [])
        return all_articles