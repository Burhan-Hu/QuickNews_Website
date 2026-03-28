import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil import parser as date_parser
import time
import re
import html

class HTMLNewsFetcher:
    """
    国内网站HTML直接抓取（绕过过期RSS）- 修复版
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
                            'image_url': images[0]['url'] if images else None,
                            'images': images,
                            'videos': videos,
                            'category_hint': 'international',
                            'country_hint': 'HK',
                            'fetch_method': 'html_scmp'
                        })
                        print(f"  [Debug] SCMP ✓ 成功: {link} ({len(images)}图)")
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
        
            if is_video_page:
                return self._fetch_cnn_video_page(soup, url)
            else:
                return self._fetch_cnn_article_page(soup, url)
            
        except Exception as e:
            print(f"    [Error] CNN详情页失败: {e}")
            return '', datetime.now(), [], []

    def _fetch_cnn_video_page(self, soup, url):
        """CNN视频页解析：提取视频信息、缩略图和简短描述"""
        content = ''
        images = []
        videos = []
        pub_time = datetime.now()
    
        # 查找视频资源组件
        video_resource = soup.find('div', {'data-component-name': 'video-resource'})
        if not video_resource:
            video_resource = soup.find('div', {'class': 'video-resource'})
    
        if video_resource:
            # 提取标题（data-headline）
            title = video_resource.get('data-headline', '').strip()
        
            # 提取描述（HTML解码）
            import html
            desc_html = video_resource.get('data-description', '')
            if desc_html:
                # 去除HTML标签，保留纯文本
                desc_soup = BeautifulSoup(html.unescape(desc_html), 'lxml')
                content = desc_soup.get_text(strip=True)
        
            # 提取时间
            pub_date = video_resource.get('data-publish-date', '')
            if pub_date:
                try:
                    pub_time = datetime.strptime(pub_date[:19], '%Y-%m-%dT%H:%M:%S')
                except:
                    pass
        
            # 提取缩略图（优先使用 poster-image-override，其次是 fave-thumbnails）
            poster_data = video_resource.get('data-poster-image-override', '')
            if poster_data:
                try:
                    import json
                    poster_json = json.loads(poster_data.replace('&quot;', '"'))
                    if 'big' in poster_json and 'uri' in poster_json['big']:
                        img_url = poster_json['big']['uri']
                        if 'media.cnn.com' in img_url:
                            images.append({
                                'url': img_url,
                                'alt': title,
                                'caption': title
                            })
                except:
                    pass
        
            # 如果没找到，尝试 fave-thumbnails
            if not images:
                thumbs_data = video_resource.get('data-fave-thumbnails', '')
                if thumbs_data:
                    try:
                        thumbs_data = thumbs_data.replace('&quot;', '"')
                        import json
                        thumbs_json = json.loads(thumbs_data)
                        if 'big' in thumbs_json and 'uri' in thumbs_json['big']:
                            img_url = thumbs_json['big']['uri']
                            if 'media.cnn.com' in img_url:
                                images.append({
                                    'url': img_url,
                                    'alt': title,
                                    'caption': title
                                })
                    except:
                        pass
        
            # 标记为视频类型
            if content:
                videos.append({
                    'url': url,  # 页面URL即视频页URL
                    'type': 'video_page',
                    'platform': 'cnn',
                    'title': title
                })
    
        # 如果上面没找到内容，尝试备用方案：查找video-player组件中的poster
        if not content:
            video_player = soup.find('div', {'data-component-name': 'video-player'})
            if video_player:
                # 尝试从video-player提取
                pass  # 逻辑已在上面覆盖大部分情况
    
        return content, pub_time, images, videos

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

    def fetch_cctv_news(self):
        """
        央视新闻HTML抓取 - 使用Playwright处理JavaScript动态加载
        """
        url = 'https://ysxw.cctv.cn/24hours.html'
        print(f"[HTML] 抓取: 央视新闻-24小时")
        
        try:
            from playwright.sync_api import sync_playwright
            
            articles = []
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                page = context.new_page()
                
                print("  [Debug] 正在加载页面...")
                page.goto(url, wait_until='networkidle', timeout=30000)
                time.sleep(3)  # 等待JS渲染
                
                rendered_html = page.content()
                soup = BeautifulSoup(rendered_html, 'lxml')
                
                # 提取新闻链接
                print(f"  [Debug] 页面HTML长度: {len(rendered_html)} 字符")
                links = self._extract_cctv_links(soup)
                print(f"  [Debug] 找到 {len(links)} 个新闻链接")
                
                # 去重处理
                seen_urls = set()
                unique_links = []
                for title, href in links:
                    href = html.unescape(href)
                    href = re.sub(r'&t=\d+', '', href)
                    if not href.startswith('http'):
                        href = 'https://ysxw.cctv.cn' + href
                    
                    if href not in seen_urls:
                        seen_urls.add(href)
                        unique_links.append((title, href))
                
                print(f"  [Debug] 去重后: {len(unique_links)} 个")
                
                # 抓取详情页
                for title, href in unique_links[:15]:
                    try:
                        content, pub_time, images, videos = self._fetch_cctv_page(page, href, title)
                        
                        if content and len(content) > 50:
                            articles.append({
                                'title': title[:300],
                                'summary': content[:500],
                                'content': content[:15000],
                                'source_url': href,
                                'source_name': '央视新闻',
                                'published_at': pub_time,
                                'image_url': images[0]['url'] if images else None,
                                'images': images,
                                'videos': videos,
                                'category_hint': 'news',
                                'country_hint': 'CN',
                                'fetch_method': 'playwright_cctv'
                            })
                            video_info = f", {len(videos)}视频" if videos else ", 无视频"
                            print(f"    ✓ {title[:30]}... ({len(content)}字, {len(images)}图{video_info})")
                        else:
                            print(f"    ✗ 内容太短: {title[:30]}...")
                        
                        time.sleep(0.5)
                    except Exception as e:
                        print(f"    ✗ 失败: {str(e)[:50]}")
                        continue
                
                browser.close()
            
            print(f"[HTML] ✓ 央视新闻: {len(articles)} 条")
            return articles
            
        except ImportError:
            print("[HTML] ✗ 请先安装Playwright: pip install playwright")
            print("            然后运行: playwright install chromium")
            return []
        except Exception as e:
            print(f"[HTML] ✗ 央视新闻: {e}")
            return []
    
    def _extract_cctv_links(self, soup):
        """提取央视新闻链接"""
        links = []
        
        # 策略1: 通过 item_id 查找
        all_a = soup.find_all('a', href=True)
        print(f"    [LinkDebug] 页面总链接数: {len(all_a)}")
        
        for a in all_a:
            href = a.get('href', '')
            if 'item_id=' in href:
                title = a.get_text(strip=True)
                if title and len(title) > 3:
                    links.append((title, href))
        
        print(f"    [LinkDebug] item_id链接: {len(links)} 个")
        
        if links:
            return links
        
        # 策略2: 卡片类名
        for pattern in ['card', 'item', 'news']:
            cards = soup.find_all('a', class_=re.compile(pattern, re.I))
            print(f"    [LinkDebug] 类名'{pattern}'匹配: {len(cards)} 个")
            for card in cards:
                href = card.get('href', '')
                title = card.get_text(strip=True)
                if title and len(title) > 3 and href:
                    links.append((title, href))
            if links:
                break
        
        return links
    
    def _fetch_cctv_page(self, page, url, list_title=''):
        """使用Playwright抓取详情页 - 修复视频抓取（深度提取M3U8）"""
        page.goto(url, wait_until='networkidle', timeout=15000)
        time.sleep(3)  # 增加等待时间，确保视频加载
        
        html_content = page.content()
        soup = BeautifulSoup(html_content, 'lxml')
        
        # 标题
        title = list_title
        h1 = soup.find('h1')
        if h1:
            page_title = h1.get_text(strip=True)
            if page_title and len(page_title) > 5:
                title = page_title
        
        # 时间
        pub_time = datetime.now()
        time_elem = soup.find('span', class_='time') or soup.select_one('[class*="time"]')
        if time_elem:
            time_text = time_elem.get_text(strip=True)
            match = re.search(r'(\d{4}[-/]\d{2}[-/]\d{2}[\s:]\d{2}:\d{2})', time_text)
            if match:
                try:
                    time_str = match.group(1).replace('/', '-')
                    pub_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M')
                except:
                    pass
        
        # 正文
        content = ''
        content_div = soup.find('div', class_='article-content')
        if content_div:
            for tag in content_div.find_all(['script', 'style', 'iframe']):
                tag.decompose()
            
            texts = []
            for p in content_div.find_all('p'):
                text = p.get_text(strip=True)
                if text and len(text) > 5:
                    if not any(x in text for x in ['版权所有', '©']):
                        texts.append(text)
            content = '\n\n'.join(texts)
        
        # 图片
        images = []
        if content_div:
            for img in content_div.find_all('img'):
                src = img.get('src', '') or img.get('data-src', '')
                if src and not src.endswith('.gif'):
                    images.append({'url': src, 'alt': title, 'caption': title})
        
        # 视频 - 深度提取M3U8源
        videos = []
        cover_url = ''
        
        print(f"    [VideoDebug] 开始提取视频...")
        
        # 策略1: 查找.prism-cover获取封面图（阿里云播放器）
        prism_cover = soup.find('div', class_='prism-cover')
        if prism_cover:
            style = prism_cover.get('style', '')
            cover_match = re.search(r'url\(["\']?([^"\')]+)', style)
            if cover_match:
                cover_url = cover_match.group(1).replace('&quot;', '').strip()
                print(f"    [VideoDebug] 找到封面图: {cover_url[:60]}...")
        
        # 检查是否有视频播放器
        has_player = bool(soup.find('div', class_='prism-player') or 
                         soup.find('div', class_='video-player-wrap') or
                         soup.find('video'))
        print(f"    [VideoDebug] 检测到视频播放器: {has_player}")
        
        # 策略2: 从所有script标签中深度提取视频配置
        all_scripts = ''
        for script in soup.find_all('script'):
            if script.string:
                all_scripts += script.string + '\n'
        
        # 查找M3U8链接（多种模式）
        video_sources = []
        
        # 模式1: 直接匹配M3U8 URL
        m3u8_patterns = [
            r'(https?://[^\s"\'\]\>\,]+\.m3u8[^\s"\'\]\>\,]*)',
            r'(https?://[^\s"\'\]\>\,]+\/index\.m3u8)',
            r'["\'](https?://[^"\']+\.m3u8)["\']',
        ]
        for pattern in m3u8_patterns:
            matches = re.findall(pattern, all_scripts)
            for m in matches:
                if m and m not in video_sources:
                    video_sources.append(m)
        
        if video_sources:
            print(f"    [VideoDebug] 从脚本中找到 {len(video_sources)} 个M3U8源")
            for i, vs in enumerate(video_sources[:2]):
                print(f"      - 源{i+1}: {vs[:70]}...")
        
        # 模式2: 查找视频配置对象（JSON格式）
        config_patterns = [
            r'video[\s]*[:=][\s]*["\']([^"\']+)["\']',
            r'src[\s]*[:=][\s]*["\']([^"\']*\.m3u8[^"\']*)["\']',
            r'url[\s]*[:=][\s]*["\']([^"\']*\.m3u8[^"\']*)["\']',
            r'playUrl[\s]*[:=][\s]*["\']([^"\']+)["\']',
            r'videoUrl[\s]*[:=][\s]*["\']([^"\']+)["\']',
        ]
        for pattern in config_patterns:
            matches = re.findall(pattern, all_scripts)
            for m in matches:
                if m and '.m3u8' in m and m not in video_sources:
                    video_sources.append(m)
                    print(f"    [VideoDebug] 从配置中找到源: {m[:60]}...")
        
        # 模式3: 尝试用Playwright执行JS获取视频源
        js_video_found = False
        try:
            video_info = page.evaluate('''() => {
                const videos = document.querySelectorAll('video');
                const result = [];
                videos.forEach(v => {
                    result.push({
                        src: v.src,
                        currentSrc: v.currentSrc,
                        poster: v.poster
                    });
                });
                if (window.player && window.player.getCurrentQuality) {
                    result.push({playerSrc: 'player-exists'});
                }
                if (window.videoInfo) {
                    result.push({videoInfo: window.videoInfo});
                }
                return result;
            }''')
            
            print(f"    [VideoDebug] JS找到 {len(video_info)} 个video元素")
            
            for info in video_info:
                if info.get('currentSrc'):
                    print(f"    [VideoDebug] video.currentSrc: {info['currentSrc'][:60]}...")
                    if '.m3u8' in info['currentSrc'] and info['currentSrc'] not in video_sources:
                        video_sources.append(info['currentSrc'])
                        js_video_found = True
                if info.get('src') and info['src'] not in video_sources:
                    print(f"    [VideoDebug] video.src: {info['src'][:60]}...")
                    if '.m3u8' in info['src']:
                        video_sources.append(info['src'])
                        js_video_found = True
                if info.get('poster') and not cover_url:
                    cover_url = info['poster']
        except Exception as e:
            print(f"    [VideoDebug] JS执行失败: {e}")
        
        # 构建视频列表
        if video_sources:
            for vs in video_sources[:3]:
                videos.append({
                    'url': vs,
                    'type': 'm3u8',
                    'platform': 'cctv',
                    'poster': cover_url
                })
        
        # 如果没有任何视频源但有播放器，添加占位
        if not videos:
            if has_player:
                videos.append({
                    'url': url,  # 使用文章URL作为视频页链接
                    'type': 'video_page',
                    'platform': 'cctv',
                    'poster': cover_url,
                    'note': '视频需通过原页面播放'
                })
                print(f"    [VideoDebug] 未提取到视频源，但检测到播放器，添加占位")
            else:
                print(f"    [VideoDebug] 未检测到视频")
        else:
            print(f"    [VideoDebug] 最终提取到 {len(videos)} 个视频")
        
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
                    
                    # 提取正文
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
                    
                    # 修复图片提取 - ScienceDaily使用相对路径 /images/
                    images = []
                    for img in article_soup.select('#text img, .lead img, [itemprop="articleBody"] img, .main-content img'):
                        src = img.get('src', '')
                        if src and not src.endswith('.gif'):
                            # 补全URL（关键修复：ScienceDaily图片是相对路径 /images/...）
                            if src.startswith('/'):
                                src = 'https://www.sciencedaily.com' + src
                            elif not src.startswith('http'):
                                src = 'https://www.sciencedaily.com/' + src
                            
                            alt = img.get('alt', '')
                            # 排除图标类图片
                            if any(x in src.lower() for x in ['icon', 'logo', 'button']):
                                continue
                                
                            images.append({
                                'url': src, 
                                'alt': alt, 
                                'caption': img.get('title', alt)
                            })
                    
                    # 视频提取
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
                        
                        # 提取视频
                        videos = []
                        for iframe in article_soup.find_all('iframe'):
                            src = iframe.get('src', '')
                            if src:
                                if src.startswith('//'):
                                    src = 'https:' + src
                                videos.append({
                                    'url': src,
                                    'type': 'iframe',
                                    'platform': 'nytimes'
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

    def fetch_all_domestic(self):
        """抓取所有国内外源"""
        all_articles = []
        
        # 新华网
        all_articles.extend(self.fetch_xinhua())

        # 南华早报
        all_articles.extend(self.fetch_scmp())
        # 央视新闻
        all_articles.extend(self.fetch_cctv_news() or [])
        # CNN
        all_articles.extend(self.fetch_cnn())

        # Al Jazeera
        all_articles.extend(self.fetch_aljazeera())

        # 环球时报
        all_articles.extend(self.fetch_globaltimes())
        
        return all_articles
    
    def fetch_all_html_sources(self):
        """抓取所有HTML源（包括国内和国际）"""
        all_articles = []
        
        # 国内源
        all_articles.extend(self.fetch_cctv_news() or [])
        all_articles.extend(self.fetch_xinhua() or [])
        all_articles.extend(self.fetch_scmp() or [])
        all_articles.extend(self.fetch_cnn() or [])
        all_articles.extend(self.fetch_globaltimes() or [])
        
        # 国际源（替代RSS）
        all_articles.extend(self.fetch_sciencedaily() or [])
        time.sleep(1)
        all_articles.extend(self.fetch_sputnik() or [])
        time.sleep(1)
        all_articles.extend(self.fetch_nytimes_cn() or [])
        time.sleep(1)
        all_articles.extend(self.fetch_aljazeera() or [])
        return all_articles
