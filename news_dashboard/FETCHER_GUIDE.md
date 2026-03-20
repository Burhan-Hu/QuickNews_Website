# 新闻爬虫快速使用指南

## 📋 概述

已为你创建了两个新闻爬虫模块：
- **Al Jazeera 爬虫** (`aljazeera_fetcher.py`) - 英文国际新闻
- **环球时报爬虫** (`globaltimes_fetcher.py`) - 中文国际新闻

## 🚀 快速开始

### 1. 测试爬虫

```bash
cd d:\qknews\news_dashboard\core

# 测试所有爬虫
python test_fetchers.py --all

# 只测试 Al Jazeera
python test_fetchers.py --aljazeera

# 只测试环球时报
python test_fetchers.py --globaltimes

# 导出示例数据
python test_fetchers.py --export
```

### 2. 在代码中使用

#### Al Jazeera 爬虫

```python
from aljazeera_fetcher import AlJazeeraFetcher

# 创建爬虫实例
fetcher = AlJazeeraFetcher(delay=2.0)  # delay: 请求间隔秒数

# 爬取单篇文章
article = fetcher.fetch_article('https://www.aljazeera.com/news/2026/3/19/...')

print(f"标题: {article['title']}")
print(f"作者: {article['author']}")
print(f"发布时间: {article['publish_date']}")
print(f"图片: {len(article['images'])} 张")
print(f"视频: {len(article['videos'])} 个")
print(f"正文: {article['content'][:200]}...")

# 爬取新闻列表
articles = fetcher.fetch_list(category='news')  # news, sports, features, opinions
for article in articles:
    print(f"- {article['title']}")
    print(f"  URL: {article['url']}")
```

#### 环球时报爬虫

```python
from globaltimes_fetcher import GlobalTimesFetcher

# 创建爬虫实例
fetcher = GlobalTimesFetcher(delay=2.0)

# 爬取单篇文章
article = fetcher.fetch_article('https://www.globaltimes.cn/page/202603/1357248.shtml')

print(f"标题: {article['title']}")
print(f"作者: {article['author']}")
print(f"发布时间: {article['publish_date']}")
print(f"图片: {len(article['images'])} 张")
print(f"视频: {len(article['videos'])} 个")

# 爬取新闻列表（国际频道）
articles = fetcher.fetch_list(channel='world')  # world, china, home, opinion, in-depth

# 爬取首页推荐
highlights = fetcher.fetch_highlights()

# 解析时间
from datetime import datetime
parsed_time = GlobalTimesFetcher.parse_datetime("Mar 20, 2026 12:04 AM")
print(f"解析结果: {parsed_time}")
```

## 📊 返回数据格式

### 单篇文章数据结构

```python
{
    'source': 'Al Jazeera' 或 'Global Times',
    'url': 'https://...',
    'title': '文章标题',
    'author': '作者名称',
    'publish_date': '2026-03-19T...' 或 'Mar 20, 2026 12:04 AM',
    'content': '正文内容...',
    'images': [
        {
            'src': 'https://example.com/image.jpg',
            'alt': '图片说明',
            'title': '图片标题'
        },
        ...
    ],
    'videos': [
        {
            'src': 'https://www.youtube.com/embed/...',
            'type': 'iframe'
        },
        ...
    ],
    'category': 'news' 或其他,
    'fetched_at': '2026-03-20T12:34:56.789123',
    'error': None  # 如果出错会包含错误信息
}
```

### 列表数据结构

```python
[
    {
        'title': '文章标题',
        'url': 'https://...',
        'category': '分类名称',
        'channel': '频道名称'  # 仅环球时报
    },
    ...
]
```

## 🔍 CSS 选择器参考

### Al Jazeera 关键选择器

| 元素 | 选择器 | 说明 |
|------|--------|------|
| 标题 | `h1` | 文章主标题 |
| 作者 | `a[href*="/author/"]` | 作者链接 |
| 时间 | `time` | 发布时间（含 datetime 属性） |
| 正文 | `article` | 主文章容器 |
| 图片 | `article img` | 文章内图片 |
| 视频 | `iframe[src*="youtube"]` | YouTube 嵌入 |

### 环球时报关键选择器

| 元素 | 选择器 | 说明 |
|------|--------|------|
| 标题 | `h1` | 文章主标题 |
| 作者 | `a[href*="/author/"]` | 作者链接 |
| 时间 | `[class*="date"]` | 发布时间周围的元素 |
| 正文 | `article` | 主文章容器 |
| 图片 | `img[src*="/Portals/"]` | CDN 图片链接 |
| 视频 | `iframe[src*="youtube"]` | YouTube 嵌入 |

## 🛠️ 集成到现有项目

### 修改 `news_dashboard/core/fetcher.py`

将两个爬虫集成到主 fetcher：

```python
from aljazeera_fetcher import AlJazeeraFetcher
from globaltimes_fetcher import GlobalTimesFetcher

class FetcherManager:
    def __init__(self):
        self.aljazeera = AlJazeeraFetcher(delay=2.0)
        self.globaltimes = GlobalTimesFetcher(delay=2.0)
    
    def fetch_all_news(self):
        """从所有源爬取新闻"""
        all_articles = []
        
        # Al Jazeera
        aj_news = self.aljazeera.fetch_list('news')
        for item in aj_news:
            article = self.aljazeera.fetch_article(item['url'])
            all_articles.append(article)
        
        # Global Times
        gt_news = self.globaltimes.fetch_list('world')
        for item in gt_news:
            article = self.globaltimes.fetch_article(item['url'])
            all_articles.append(article)
        
        return all_articles
```

## ⚙️ 配置选项

### 请求延迟 (delay)

```python
# 默认: 2.0 秒
fetcher = AlJazeeraFetcher(delay=2.0)

# 更快: 1.0 秒 (风险：可能被封IP)
fetcher = AlJazeeraFetcher(delay=1.0)

# 更慢: 5.0 秒 (更安全)
fetcher = AlJazeeraFetcher(delay=5.0)
```

### 分类和频道

**Al Jazeera 分类**:
- `news` - 新闻
- `sports` - 体育
- `features` - 特稿
- `opinions` - 观点
- `economy` - 经济

**环球时报频道**:
- `world` - 国际（推荐）
- `china` - 中国
- `home` - 首页
- `opinion` - 观点
- `in-depth` - 深度

## 🔴 常见问题

### 1. 请求超时

**问题**: `requests.exceptions.Timeout`

**解决方案**:
```python
fetcher = AlJazeeraFetcher(delay=2.0)
# 增加超时时间在 fetch_article 中修改 timeout=10
```

### 2. 页面加载不完整（Al Jazeera）

**问题**: 首页列表无法获取

**原因**: Al Jazeera 首页使用 React 动态加载

**解决方案**:
- 使用 Selenium 或 Playwright 处理 JavaScript
- 直接爬取分类页面 URL
- 使用 API（如果有公开的）

示例：
```python
# 使用 Selenium 处理 JavaScript
from selenium import webdriver

driver = webdriver.Chrome()
driver.get('https://www.aljazeera.com/news/')
# 等待页面加载
# ... 处理动态内容
```

### 3. 环球时报中文编码问题

**问题**: 出现乱码

**解决方案**: 已在爬虫中设置 `resp.encoding = 'utf-8'`，确保数据库也使用 UTF-8

```python
# 数据库连接
import pymysql
conn = pymysql.connect(..., charset='utf8mb4')
```

### 4. 图片 URL 无法访问

**问题**: CDN 返回 403

**解决方案**: 添加 Referer 头

```python
headers = {
    'User-Agent': 'Mozilla/5.0...',
    'Referer': 'https://www.globaltimes.cn/'  # 或 'https://www.aljazeera.com/'
}
```

## 📈 性能优化建议

### 1. 批量爬取优化

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_multiple_articles(urls, max_workers=3):
    fetcher = AlJazeeraFetcher(delay=0.5)  # 减少delay，并关闭线程
    
    articles = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetcher.fetch_article, url): url for url in urls}
        for future in as_completed(futures):
            try:
                article = future.result()
                articles.append(article)
            except Exception as e:
                print(f"Error: {e}")
    
    return articles
```

### 2. 缓存策略

```python
import json
from datetime import datetime, timedelta

def cached_fetch(url, cache_file='cache.json', ttl_hours=24):
    # 检查缓存
    try:
        with open(cache_file, 'r') as f:
            cache = json.load(f)
        if url in cache:
            cached_time = datetime.fromisoformat(cache[url]['cached_at'])
            if datetime.now() - cached_time < timedelta(hours=ttl_hours):
                return cache[url]['data']
    except FileNotFoundError:
        cache = {}
    
    # 爬取新数据
    fetcher = AlJazeeraFetcher()
    data = fetcher.fetch_article(url)
    
    # 保存缓存
    cache[url] = {
        'data': data,
        'cached_at': datetime.now().isoformat()
    }
    with open(cache_file, 'w') as f:
        json.dump(cache, f)
    
    return data
```

### 3. 错误处理和重试

```python
import time

def fetch_with_retry(url, max_retries=3, backoff=2):
    fetcher = AlJazeeraFetcher()
    
    for attempt in range(max_retries):
        try:
            return fetcher.fetch_article(url)
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = backoff ** attempt
                print(f"重试 {attempt + 1}/{max_retries - 1}，等待 {wait_time} 秒...")
                time.sleep(wait_time)
            else:
                return {'error': str(e), 'url': url, 'attempts': max_retries}
```

## 📝 日志记录

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('news_fetcher.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('AlJazeeraFetcher')
logger.info('开始爬取...')
```

## 🔗 相关资源

- [Beautiful Soup 文档](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Requests 库文档](https://requests.readthedocs.io/)
- [CSS 选择器参考](https://www.w3schools.com/cssref/default.asp)
- [XPath 参考](https://www.w3schools.com/xml/xpath_intro.asp)

## ⚖️ 法律和道德

- ✅ 遵守网站的 `robots.txt`
- ✅ 设置合理的请求延迟
- ✅ 检查网站的服务条款
- ✅ 不爬取用户个人信息
- ❌ 不要用于商业目的（除非获得授权）
- ❌ 不要进行大规模滥用爬虫

---

**创建时间**: 2026-03-20  
**爬虫版本**: 1.0  
**维护者**: AI Assistant
