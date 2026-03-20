import requests
import feedparser
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from config.sources import NEWSAPI_CONFIG, RSS_SOURCES, rotator
import time

class NewsFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def _fetch_full_page_content(self, url):
        """从源URL抓取详情页全文（NewsAPI口径 content 截断时备用）"""
        try:
            resp = self.session.get(url, timeout=12)
            resp.raise_for_status()
            resp.encoding = resp.encoding or 'utf-8'
            html = resp.text
        except Exception as e:
            print(f"  [NewsAPI-fallback] 无法获取网页: {e}")
            return ''

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')

        # 付费墙/登录墙关键词（高信号，不影响正常全文）
        hard_paywall_signals = [
            '请先登录', '登录后可见', '请先订阅', '付费后查看', '仅会员', '仅VIP',
            '需要购买', '订阅后可见', 'subscribe to continue', 'sign in to continue',
            'you must login', 'you must sign in', 'you must subscribe', 'paywall'
        ]

        def is_paywall_content(text: str) -> bool:
            low = text.lower()
            matched = [sig for sig in hard_paywall_signals if sig in low]
            # 如果页面文本里包含付费墙提示且正文长度较短，则认为是付费墙页面
            if matched and len(text) < 100:
                return True
            return False

        # 优先尝试最常见容器
        selectors = [
            'div.article', 'div#content', 'div.main', 'article',
            'div#article-content', 'div.content', 'div#main',
            'div#p-detail', 'div.news-detail', 'section.article',
        ]

        for sel in selectors:
            node = soup.select_one(sel)
            if node:
                paragraphs = node.find_all('p')
                texts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
                content = '\n\n'.join(texts)
                if content and not is_paywall_content(content) and len(content) > 200:
                    return content

        # 兜底：全页 p 提取
        paragraphs = soup.find_all('p')
        texts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
        content = '\n\n'.join(texts)
        if content and not is_paywall_content(content) and len(content) > 250:
            return content

        # 如果内容短且可能是付费提示，则判定为失败
        if content and is_paywall_content(content):
            print(f"  [NewsAPI-fallback] 可能付费墙内容（正文短且含付费提示），跳过: {url}")
            return ''

        # 再尝试 meta description，仍作为兜底（不会算作高质量全文）
        meta_desc = soup.select_one('meta[name=description]') or soup.select_one('meta[property="og:description"]')
        if meta_desc:
            desc = meta_desc.get('content', '').strip()
            if desc and not is_paywall_content(desc) and len(desc) > 50:
                return desc

        return ''

    def fetch_newsapi(self):
        """获取NewsAPI数据"""
        params_data = rotator.get_next_params()
        if not params_data:
            print("[NewsAPI] 已达到每日请求上限(100次)")
            return [], None

        params, category, country = params_data

        try:
            url = f"{NEWSAPI_CONFIG['base_url']}/top-headlines"
            print(f"[NewsAPI] 请求: {category}/{country}")

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('status') != 'ok':
                print(f"[NewsAPI] API错误: {data.get('message', '未知错误')}")
                return [], None

            articles = []
            for item in data.get('articles', []):
                pub_time = datetime.now()
                if item.get('publishedAt'):
                    try:
                        pub_time = date_parser.parse(item['publishedAt'])
                    except:
                        pass

                raw_content = item.get('content') or item.get('description') or ''
                if raw_content and raw_content.endswith('...'):
                    raw_content = item.get('description', raw_content)

                from html.parser import HTMLParser
                class MLStripper(HTMLParser):
                    def __init__(self):
                        super().__init__()
                        self.reset()
                        self.fed = []
                    def handle_data(self, d):
                        self.fed.append(d)
                    def get_data(self):
                        return ''.join(self.fed)

                def strip_tags(html_txt):
                    s = MLStripper()
                    try:
                        s.feed(html_txt)
                        return s.get_data()
                    except:
                        return html_txt

                content_text = strip_tags(raw_content) if raw_content else ''

                # 当返回内容过短或末尾截断时尝试二次抓取全文
                need_fallback = (not content_text) or len(content_text) < 220 or content_text.endswith('...')
                source_url = item.get('url', '')
                fallback_failed = False
                if need_fallback and source_url:
                    full_content = self._fetch_full_page_content(source_url)
                    if full_content and len(full_content) > len(content_text):
                        content_text = full_content
                    else:
                        # 对于403/404等页面访问失败或者内容仍不可用，标记失败
                        if not full_content:
                            fallback_failed = True

                content_text = (content_text or '').strip()

                # 如果没有可用内容，则跳过该条目，避免存入不完整数据
                if not content_text or fallback_failed:
                    print(f"[NewsAPI] ✗ 跳过条目（无正文或抓取失败）: {item.get('title', '')[:30]}")
                    continue

                articles.append({
                    'title': item.get('title', '') or '无标题',
                    'summary': content_text[:500],
                    'content': content_text[:15000],
                    'source_url': source_url,
                    'source_name': item.get('source', {}).get('name', 'NewsAPI'),
                    'published_at': pub_time,
                    'image_url': item.get('urlToImage'),
                    'category_hint': category,
                    'country_hint': country,
                    'fetch_method': 'newsapi'
                })

            print(f"[NewsAPI] ✓ 成功获取 {len(articles)} 条 [{category}/{country}]")
            status = rotator.get_status()
            # 修复：ensure status有必要字段
            if status and isinstance(status, dict):
                if 'next_country' not in status:
                    status['next_country'] = 'N/A'
                if 'next_category' not in status:
                    status['next_category'] = 'N/A'
            return articles, status

        except Exception as e:
            print(f"[NewsAPI] ✗ 失败: {e}")
            return [], None
    
    def fetch_rss(self, source_config):
        """获取单个RSS源（严格48小时限制）"""
        cutoff_time = datetime.now() - timedelta(hours=48)  # 严格48小时
    
        try:
            print(f"[RSS] 获取: {source_config['name']}")
        
            response = self.session.get(
                source_config['url'], 
                timeout=15,
                headers={'Accept': 'application/rss+xml, application/xml, text/xml, */*'}
            )
            response.raise_for_status()
        
            feed = feedparser.parse(response.content)
            print(f"  [Debug] {source_config['name']} 原始条目数: {len(feed.entries)}")
        
            articles = []
        
            for entry in feed.entries[:20]:
                try:
                    # 严格时间解析
                    pub_time = None
                
                    # 尝试多种时间字段
                    time_fields = ['published', 'updated', 'pubDate', 'dc:date']
                    for field in time_fields:
                        if hasattr(entry, field) and getattr(entry, field):
                            try:
                                pub_time = date_parser.parse(getattr(entry, field))
                                # 去除时区
                                if pub_time.tzinfo:
                                    pub_time = pub_time.replace(tzinfo=None)
                                break
                            except Exception as e:
                                continue
                
                    # 如果无法解析时间，跳过该条目（避免入库旧数据）
                    if not pub_time:
                        print(f"  [Debug] 跳过：无法解析时间 - {entry.get('title', '无标题')[:30]}")
                        continue
                
                    # 严格检查：必须在未来48小时内
                    if pub_time < cutoff_time:
                        continue  # 太旧，跳过
                
                    # 如果时间是未来时间（某些RSS错误），调整为当前时间
                    if pub_time > datetime.now():
                        pub_time = datetime.now()
                
                    # 提取其他字段...
                    image_url = None
                    if hasattr(entry, 'media_content') and entry.media_content:
                        image_url = entry.media_content[0].get('url')
                    elif hasattr(entry, 'enclosures') and entry.enclosures:
                        image_url = entry.enclosures[0].get('url')
                
                    # 提取内容（优先使用content，次之summary）
                    content = ''
                    if hasattr(entry, 'content') and entry.content:
                        content = entry.content[0].get('value', '')
                    elif hasattr(entry, 'summary'):
                        content = entry.summary
                    
                    # 清理HTML标签
                    from html.parser import HTMLParser
                    class MLStripper(HTMLParser):
                        def __init__(self):
                            super().__init__()
                            self.reset()
                            self.fed = []
                        def handle_data(self, d):
                            self.fed.append(d)
                        def get_data(self):
                            return ''.join(self.fed)
                    
                    def strip_tags(html):
                        s = MLStripper()
                        try:
                            s.feed(html)
                            return s.get_data()
                        except:
                            return html
                    
                    content_text = strip_tags(content) if content else ''
                    
                    articles.append({
                        'title': entry.get('title', '无标题')[:300],
                        'summary': content_text[:500],
                        'content': content_text[:15000],  # 完整内容，限制1.5万字
                        'source_url': entry.get('link', ''),
                        'source_name': source_config['name'],
                        'published_at': pub_time,
                        'image_url': image_url,
                        'category_hint': source_config.get('category', 'general'),
                        'country_hint': source_config.get('country_hint'),  # 部分源预设国家
                        'fetch_method': 'rss'
                    })
                
                except Exception as e:
                    continue
        
            print(f"[RSS] ✓ {source_config['name']}: {len(articles)} 条 (48h内)")
            return articles
        
        except Exception as e:
            print(f"[RSS] ✗ {source_config['name']}: {str(e)[:50]}")
            return []
    
    def fetch_all_rss(self):
        """获取所有RSS源"""
        all_articles = []
        for source in RSS_SOURCES:
            articles = self.fetch_rss(source)
            if articles:
                all_articles.extend(articles)
            time.sleep(0.5)
        return all_articles
    def fetch_html_domestic(self):
        """国内网站HTML抓取"""
        from core.html_fetcher import HTMLNewsFetcher
        html_fetcher = HTMLNewsFetcher()
        return html_fetcher.fetch_all_domestic()