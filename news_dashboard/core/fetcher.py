import requests
import feedparser
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from html.parser import HTMLParser
from config.sources import NEWSAPI_CONFIG, RSS_SOURCES, rotator
import time


class MLStripper(HTMLParser):
    """HTML标签清洗器"""
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)


def strip_tags(html):
    """去除HTML标签"""
    if not html:
        return ''
    s = MLStripper()
    try:
        s.feed(html)
        return s.get_data()
    except:
        return html


class NewsFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        # 初始化HTML抓取器，供流式处理使用
        from core.html_fetcher import HTMLNewsFetcher
        self.html_fetcher = HTMLNewsFetcher()
    
    def _fetch_full_page_content(self, url):
        """从源URL抓取详情页全文（仅清洗HTML，不做长度判断）"""
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
                # 仅保留非空检查，长度检查交给SQL触发器
                if content:
                    return content

        # 兜底：全页 p 提取
        paragraphs = soup.find_all('p')
        texts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
        return '\n\n'.join(texts)

    def fetch_newsapi(self):
        """获取NewsAPI数据（移除长度检查，仅做数据抓取和格式清洗）"""
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
                try:
                    pub_time = datetime.now()
                    if item.get('publishedAt'):
                        try:
                            pub_time = date_parser.parse(item['publishedAt'])
                        except:
                            pass

                    raw_content = item.get('content') or item.get('description') or ''
                    article_url = item.get('url', '')
                    
                    # 判断是否需要二次抓取完整内容
                    needs_full_fetch = False
                    if raw_content:
                        if '...' in raw_content and '[' in raw_content and ('chars' in raw_content.lower() or 'char' in raw_content.lower()):
                            needs_full_fetch = True
                        if len(raw_content) < 500:
                            needs_full_fetch = True
                    else:
                        needs_full_fetch = True
                    
                    content_text = ''
                    
                    # 优先尝试从原文链接抓取完整内容
                    if needs_full_fetch and article_url:
                        print(f"  [NewsAPI] 抓取完整内容: {article_url[:60]}...")
                        full_content = self._fetch_full_page_content(article_url)
                        if full_content and len(full_content) > 200:
                            content_text = full_content
                            print(f"    ✓ 抓取成功: {len(content_text)} 字")
                        else:
                            # 二次抓取失败，跳过此条新闻
                            print(f"    ✗ 二次抓取失败，跳过此条新闻: {article_url[:60]}...")
                            continue
                    else:
                        # 不需要二次抓取
                        content_text = strip_tags(raw_content) if raw_content else ''
                    
                    if not content_text:
                        continue

                    articles.append({
                        'title': item.get('title', '') or '无标题',
                        'content': content_text[:20000],
                        'source_url': article_url,
                        'source_name': item.get('source', {}).get('name', 'NewsAPI'),
                        'published_at': pub_time,
                        'image_url': item.get('urlToImage'),
                        'category_hint': category,
                        'country_hint': country,
                        'fetch_method': 'newsapi'
                    })
                    
                    # 礼貌间隔
                    if needs_full_fetch:
                        time.sleep(0.5)
                        
                except Exception as e:
                    # 单个文章处理失败，继续下一个
                    print(f"  [NewsAPI] 单条处理失败，跳过: {str(e)[:50]}")
                    continue

            print(f"[NewsAPI] ✓ 成功获取 {len(articles)} 条 [{category}/{country}]")
            status = rotator.get_status()
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
        """获取单个RSS源（移除48小时严格限制和长度检查，仅做数据抓取）"""
        # 注意：48小时限制移至SQL的Event Scheduler或存储过程，Python不做过滤
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
                    # 时间解析（保留，因为这是元数据）
                    pub_time = None
                    time_fields = ['published', 'updated', 'pubDate', 'dc:date']
                    for field in time_fields:
                        if hasattr(entry, field) and getattr(entry, field):
                            try:
                                pub_time = date_parser.parse(getattr(entry, field))
                                if pub_time.tzinfo:
                                    pub_time = pub_time.replace(tzinfo=None)
                                break
                            except:
                                continue
                
                    # 如果无法解析时间，仍保留数据（让SQL处理时间有效性）
                    if not pub_time:
                        pub_time = datetime.now()

                    # 移除48小时检查（交给SQL的WHERE created_at > DATE_SUB...或Event清理）
                
                    # 提取内容（可能包含HTML）
                    raw_content = ''
                    if hasattr(entry, 'content') and entry.content:
                        raw_content = entry.content[0].get('value', '')
                    elif hasattr(entry, 'summary'):
                        raw_content = entry.summary
                    
                    # 从正文中提取图片（支持<img src="...">格式）
                    images = []
                    if raw_content:
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(raw_content, 'lxml')
                        for img in soup.find_all('img'):
                            src = img.get('src') or img.get('data-src')
                            if src:
                                images.append({
                                    'url': src,
                                    'alt': img.get('alt', ''),
                                    'caption': img.get('alt', '')
                                })
                    
                    # 提取封面图片（RSS标准字段）
                    image_url = None
                    if hasattr(entry, 'media_content') and entry.media_content:
                        image_url = entry.media_content[0].get('url')
                    elif hasattr(entry, 'enclosures') and entry.enclosures:
                        image_url = entry.enclosures[0].get('url')
                    
                    # 如果没有封面但有正文图片，使用第一张作为封面
                    if not image_url and images:
                        image_url = images[0]['url']
                
                    # 清理HTML标签获取纯文本内容
                    content_text = strip_tags(raw_content) if raw_content else ''
                    
                    # 不再检查长度，即使很短也传递给SQL（触发器会拦截<60的）
                    articles.append({
                        'title': entry.get('title', '无标题')[:300],
                        'content': content_text[:20000],  # 仅截断防止过大，不做质量判断
                        'source_url': entry.get('link', ''),
                        'source_name': source_config['name'],
                        'published_at': pub_time,
                        'image_url': image_url,
                        'images': images,  # 保存所有提取的图片
                        'category_hint': source_config.get('category', 'general'),  # hint only
                        'country_hint': source_config.get('country_hint'),  # hint only
                        'fetch_method': 'rss'
                    })
                
                except Exception as e:
                    continue
        
            print(f"[RSS] ✓ {source_config['name']}: {len(articles)} 条")
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
    
    def fetch_all_html_sources(self):
        """所有HTML源抓取（国内+国际）- 保持向后兼容"""
        return self.html_fetcher.fetch_all_html_sources()