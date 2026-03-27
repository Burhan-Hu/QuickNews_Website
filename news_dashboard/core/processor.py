from html.parser import HTMLParser
import re


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


class ContentProcessor:
    """
    精简版：只做HTML标签清洗和格式截断
    所有业务逻辑（长度校验/国家识别/分类/去重）都交给SQL存储过程
    """
    
    @staticmethod
    def clean_html(raw_html):
        """去除HTML标签，返回纯文本"""
        if not raw_html:
            return ''
        try:
            s = MLStripper()
            s.feed(raw_html)
            return s.get_data().strip()
        except:
            return re.sub(r'<[^>]+>', '', raw_html).strip()
    
    def process_article(self, article):
        """
        只做格式清洗和截断，所有业务校验交给SQL存储过程
        """
        content = self.clean_html(article.get('content', ''))
        title = self.clean_html(article.get('title', ''))
        
        if not content or not title:
            return None
    
        return {
            'title': title[:300],
            'content': content[:20000],  # 仅截断防止过大，不检查质量
            'source_url': article.get('source_url', '')[:800],
            'source_id': article.get('source_id', 1),
            'published_at': article.get('published_at'),
            'language': 'zh' if any('\u4e00' <= c <= '\u9fff' for c in title) else 'en',
            'hint_country': article.get('country_hint'),   # 仅作为hint
            'hint_category': article.get('category_hint'),  # 仅作为hint
            # ===== 新增：保留媒体字段 =====
            'images': article.get('images', []),
            'videos': article.get('videos', []),
            'image_url': article.get('image_url')  # 兼容单图字段（如NewsAPI）
        }