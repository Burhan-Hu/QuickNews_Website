from datetime import datetime, timedelta

# NewsAPI配置（免费版限制：100次/天，延迟一天，每次最多100条）
NEWSAPI_CONFIG = {
    'api_key': 'b57e609b94774b3bb8cc7903d735698b',  # 从newsapi.org获取
    'base_url': 'https://newsapi.org/v2',
    'requests_per_day': 100,
    'interval_seconds': 1200,  # 20分钟一次
    'page_size': 20,  # 每次取20条，避免单次过大
    'delay_days': 1   # 获取昨天的新闻（today - 1）
}

# 轮询策略：每次请求不同类别，循环覆盖
CATEGORY_ROTATION = [
    'technology',
    'business', 
    'science',
    'general',
    'health'
]

# 国家代码（NewsAPI支持）
COUNTRY_CODES = ['us', 'gb', 'jp', 'de', 'fr', 'au', 'ca', 'cn', 'in', 'kr']

# RSS源配置（作为NewsAPI补充，无限制）
RSS_SOURCES = [
    # 国内源（中文，优先）
    #{'name': '36氪', 'url': 'https://36kr.com/feed', 'lang': 'zh', 'category': 'tech'},
    #{'name': '虎嗅网', 'url': 'https://rss.aishort.top/?type=huxiu', 'lang': 'zh', 'category': 'tech'},
    # 国际源
    #{'name': 'RT-中文', 'url': 'https://www.rt.com/rss/news/', 'lang': 'en', 'category': 'international'},
    #{'name': 'FoxNews-World', 'url': 'http://feeds.foxnews.com/foxnews/world','lang': 'en', 'category': 'international','country_hint': 'US'},
    #{'name': 'FoxNews-Politics', 'url': 'http://feeds.foxnews.com/foxnews/politics','lang': 'en', 'category': 'politics','country_hint': 'US'},
    # 新增RSS源
    #{'name': 'ChinaDaily', 'url': 'https://feedx.net/rss/chinadaily.xml', 'lang': 'en', 'category': 'international'},
    #{'name': 'NewYorker', 'url': 'https://feedx.net/rss/newyorker.xml', 'lang': 'en', 'category': 'culture'},
    #{'name': '凤凰网-军事', 'url': 'https://feedx.net/rss/ifengmil.xml', 'lang': 'zh', 'category': 'military', 'country_hint': 'CN'},
    #{'name': 'AP-美联社', 'url': 'https://feedx.net/rss/ap.xml', 'lang': 'en', 'category': 'international', 'country_hint': 'US'},
    {'name': '经济日报', 'url': 'https://feedx.net/rss/jingjiribao.xml', 'lang': 'zh', 'category': 'business', 'country_hint': 'CN'}
]

# 需要HTML直接抓取的源（不从RSS读取）
HTML_SOURCES = [
    {'name': 'ScienceDaily', 'url': 'https://www.sciencedaily.com/news/', 'lang': 'en', 'category': 'science', 'country_hint': 'US'},
    {'name': '俄罗斯卫星通讯社', 'url': 'https://sputniknews.cn/', 'lang': 'zh', 'category': 'international', 'country_hint': 'RU'},
    {'name': '纽约时报-中文', 'url': 'https://cn.nytimes.com/', 'lang': 'zh', 'category': 'international', 'country_hint': 'US'},
]

class NewsAPIRotator:
    """
    NewsAPI轮询管理器：智能分配每日100次请求配额
    策略：每次请求只查询一个主题（类别），循环遍历所有类别
    """
    def __init__(self):
        self.request_count = 0
        self.category_idx = 0
        self.last_request_time = None
        
    def get_next_params(self):
        """
        返回下一次请求的参数（只查询类别，不限制国家以获取更多结果）
        策略：循环遍历所有类别
        """
        if self.request_count >= NEWSAPI_CONFIG['requests_per_day']:
            return None
            
        category = CATEGORY_ROTATION[self.category_idx % len(CATEGORY_ROTATION)]
        
        # 计算昨天日期（NewsAPI免费版延迟一天）
        yesterday = (datetime.now() - timedelta(days=NEWSAPI_CONFIG['delay_days'])).strftime('%Y-%m-%d')
        
        params = {
            'apiKey': NEWSAPI_CONFIG['api_key'],
            'category': category,
            # 移除country限制，让API返回全球该类别的新闻
            'pageSize': NEWSAPI_CONFIG['page_size'],
            'from': yesterday,
            'to': yesterday,
            'sortBy': 'publishedAt'
        }
        
        # 更新轮询索引（只循环类别）
        self.category_idx += 1
            
        self.request_count += 1
        self.last_request_time = datetime.now()
        
        return params, category, None  # country设为None
    
    def get_status(self):
        return {
            'remaining': NEWSAPI_CONFIG['requests_per_day'] - self.request_count,
            'used': self.request_count,
            'next_category': CATEGORY_ROTATION[self.category_idx % len(CATEGORY_ROTATION)]
        }

# 全局轮询器实例
rotator = NewsAPIRotator()
if not NEWSAPI_CONFIG['api_key'] or 'your-newsapi-key' in NEWSAPI_CONFIG['api_key']:
    print("[Warning] NewsAPI密钥未配置！请访问 https://newsapi.org/register 获取免费API Key")