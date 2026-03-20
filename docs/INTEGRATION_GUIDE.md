# 新网站爬取方法整合指南

## 📋 概述

已为以下4个新闻网站创建了完整的爬取方法：

1. **纽约时报中文版** (https://cn.nytimes.com/) - `fetch_nytimes`()
2. **央视网** (https://www.cctv.com/) - `fetch_cctv()`
3. **观察者网** (https://www.guancha.cn/) - `fetch_guancha()`
4. **华盛顿邮报** (https://www.washingtonpost.com/) - `fetch_washingtonpost()`

所有方法都已包含在 `NEW_SITE_FETCHERS.py` 文件中。

---

## 🔧 整合步骤

### 步骤1: 复制方法到 html_fetcher.py

打开 `news_dashboard/core/html_fetcher.py`，在 `HTMLNewsFetcher` 类中添加以下方法。

可以选择：
- **方法A**: 将 `NEW_SITE_FETCHERS.py` 中的所有方法直接复制到 `HTMLNewsFetcher` 类中
- **方法B**: 通过继承扩展 `HTMLNewsFetcher` 类

**推荐：方法A（直接复制）**

从 `NEW_SITE_FETCHERS.py` 中复制这4个方法：
```python
def fetch_nytimes(self):
    ...

def _fetch_nytimes_article(self, url):
    ...

def fetch_cctv(self):
    ...

def _fetch_cctv_article(self, url):
    ...

def fetch_guancha(self):
    ...

def _fetch_guancha_article(self, url):
    ...

def fetch_washingtonpost(self):
    ...

def _fetch_washingtonpost_article(self, url):
    ...
```

### 步骤2: 更新 fetch_all_domestic() 方法

找到 `fetch_all_domestic()` 方法（大约在文件末尾），更新其实现以包含新网站：

```python
def fetch_all_domestic(self):
    """国内网站HTML抓取 + 国际网站"""
    all_articles = []
    
    # 现有的国内网站
    all_articles.extend(self.fetch_xinhua())
    all_articles.extend(self.fetch_pengpai())
    
    # 新增：国际网站
    all_articles.extend(self.fetch_nytimes())
    all_articles.extend(self.fetch_cctv())
    all_articles.extend(self.fetch_guancha())
    all_articles.extend(self.fetch_washingtonpost())
    
    # 现有的英文网站
    all_articles.extend(self.fetch_scmp())
    all_articles.extend(self.fetch_cnn())
    
    return all_articles
```

### 步骤3: 验证和测试

在 `news_dashboard/` 目录下创建一个测试脚本 `test_new_sites.py`：

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-

from core.html_fetcher import HTMLNewsFetcher

def test_new_sites():
    fetcher = HTMLNewsFetcher()
    
    print("=" * 50)
    print("测试新网站爬取方法")
    print("=" * 50)
    
    # 测试纽约时报
    print("\n[测试1] 纽约时报中文版")
    try:
        articles = fetcher.fetch_nytimes()
        print(f"✓ 成功获取 {len(articles)} 条")
        if articles:
            print(f"  示例: {articles[0]['title'][:50]}")
    except Exception as e:
        print(f"✗ 失败: {e}")
    
    # 测试央视网
    print("\n[测试2] 央视网")
    try:
        articles = fetcher.fetch_cctv()
        print(f"✓ 成功获取 {len(articles)} 条")
        if articles:
            print(f"  示例: {articles[0]['title'][:50]}")
    except Exception as e:
        print(f"✗ 失败: {e}")
    
    # 测试观察者网
    print("\n[测试3] 观察者网")
    try:
        articles = fetcher.fetch_guancha()
        print(f"✓ 成功获取 {len(articles)} 条")
        if articles:
            print(f"  示例: {articles[0]['title'][:50]}")
    except Exception as e:
        print(f"✗ 失败: {e}")
    
    # 测试华盛顿邮报
    print("\n[测试4] 华盛顿邮报")
    try:
        articles = fetcher.fetch_washingtonpost()
        print(f"✓ 成功获取 {len(articles)} 条")
        if articles:
            print(f"  示例: {articles[0]['title'][:50]}")
    except Exception as e:
        print(f"✗ 失败: {e}")
    
    print("\n" + "=" * 50)
    print("测试完成")

if __name__ == '__main__':
    test_new_sites()
```

运行测试：
```bash
cd d:\qknews\news_dashboard
python test_new_sites.py
```

---

## 📊 各网站HTML结构速查表

### 1. 纽约时报中文版 (NYTimes)

| 项目 | 选择器/位置 | 说明 |
|------|----------|------|
| **列表页URL** | `https://cn.nytimes.com/[category]/` | 支持: china, world, business |
| **列表项** | `a[href*="/\d{8}/"]` | 日期链接模式 |
| **文章标题** | `a 的 text` | 链接文本即标题 |
| **文章链接** | `a 的 href` | 需要检查日期格式 |
| **发布时间** | `<time>` 标签或 `[data-testid*="date"]` | 完整日期时间 |
| **正文容器** | `<article>` 或 `div[class*="article"]` | 包含所有段落 |
| **正文段落** | `article > p` | 每个p是一段 |
| **图片** | `img[src*="http"]` | 需要完整URL |
| **视频** | `iframe[src*="youtube/vimeo"]` | 嵌入式视频 |

**页面示例**：
```
https://cn.nytimes.com/usa/20260320/trump-netanyahu-iran-gas-field-attack/zh-hant/
https://cn.nytimes.com/china/20260317/china-zhou-dynasty-king-climate-change/zh-hant/
```

---

### 2. 央视网 (CCTV)

| 项目 | 选择器/位置 | 说明 |
|------|----------|------|
| **新闻首页** | `https://news.cctv.com/` | 新闻频道 |
| **视频首页** | `https://v.cctv.com/` | 视频频道 |
| **列表项** | `a[href*="/\d{4}/\d{2}/\d{2}/"]` | 日期路径模式 |
| **文章标题** | `a` 的文本内容 | 链接文本 |
| **发布时间** | `span[class*="time"]` | 格式: YYYY/MM/DD HH:MM |
| **正文容器** | `div[id*="content"]` 或 `div[class*="body"]` | 关键内容容器 |
| **正文段落** | `div > p` | 段落标签 |
| **图片URL** | `img > src` | 通常: `p*.img.cctvpic.com` |
| **视频** | `<video><source src="...">` | 直接video标签或iframe |

**页面示例**：
```
https://news.cctv.com/2026/03/20/ARTIO9yk1BtpGKUTsT5Q1LxJ260320.shtml
https://v.cctv.com/2026/03/20/VIDEyiW5gC5sxjZqP5G1Qm1l260320.shtml
https://tv.cctv.com/2026/03/20/VIDEyiW5gC5sxjZqP5G1Qm1l260320.shtml
```

**视频URL的正则匹配**：
```python
# 新闻: /\d{4}/\d{2}/\d{2}/ART[A-Z0-9]+\.shtml
# 视频: /\d{4}/\d{2}/\d{2}/VIDE?[A-Z0-9]+\.shtml
```

---

### 3. 观察者网 (Guancha)

| 项目 | 选择器/位置 | 说明 |
|------|----------|------|
| **频道列表** | america, global, politics | 主要频道 |
| **列表页URL** | `https://www.guancha.cn/[channel]/` | 频道首页 |
| **列表项** | `a[href*="/\d{4}_\d{2}_\d{2}"]` | 下划线日期格式 |
| **发布时间** | `span[class*="time"]` | 同样格式 |
| **正文容器** | `article` 或 `div[class*="content"]` | 文章正文 |
| **正文段落** | `article > p` | 段落 |
| **图片** | `img[src*="http"]` | 通常是七牛云CDN |
| **视频** | `iframe[src*="bilibili/youtube"]` | 嵌入式视频 |

**页面示例**：
```
https://www.guancha.cn/america/2026_03_20_xxxxx.html
https://www.guancha.cn/global/2026_03_19_xxxxx.html
```

---

### 4. 华盛顿邮报 (Washington Post)

⚠️ **注意**：网站有反爬虫机制，且部分内容需要订阅

| 项目 | 选择器/位置 | 说明 |
|------|----------|------|
| **国际新闻** | `https://www.washingtonpost.com/world/` | World频道 |
| **美国新闻** | `https://www.washingtonpost.com/us-news/` | US频道 |
| **列表项** | `a[href*="/\d{4}/\d{2}/\d{2}/"]` | 日期路径 |
| **发布时间** | `<time>` 或 `[data-testid*="date"]` | ISO格式 |
| **正文容器** | `article` 或 `div[itemprop="articleBody"]` | 文章正文 |
| **付费墙提示** | 包含 "sign in", "subscribe" | 需要检测并跳过 |
| **图片** | `img[src*="http"]` | 通常washingtonpost-prod CDN |
| **视频** | `<video>` 标签内 `<source>` | 原生video标签 |

**页面示例**：
```
https://www.washingtonpost.com/world/2026/03/20/xxxxx/
https://www.washingtonpost.com/us-news/2026/03/20/xxxxx/
```

**反爬虫对策**：
- ✓ 使用完整 User-Agent
- ✓ 增加请求间隔 (2-3秒)
- ✓ 检测付费墙内容并跳过
- ✓ 添加 Referer 和 Accept-Language 头

---

## 🔌 数据结构

所有爬取方法返回相同的数据结构列表：

```python
{
    'title': str,              # 文章标题（≤300字符）
    'summary': str,            # 摘要（≤500字符）
    'content': str,            # 完整正文（≤15000字符）
    'source_url': str,         # 原文链接
    'source_name': str,        # 来源网站名称
    'published_at': datetime,  # 发布时间
    'image_url': str,          # 封面图片URL（可空）
    'images': list,            # 所有图片列表
    'videos': list,            # 所有视频列表
    'category_hint': str,      # 分类提示
    'country_hint': str,       # 国家代码 (CN/US/HK等)
    'fetch_method': str        # 爬取方法名称
}
```

**images 列表元素**：
```python
{
    'url': str,                # 图片URL
    'alt': str,                # 替代文本
    'caption': str             # 图片标题/描述
}
```

**videos 列表元素**：
```python
{
    'url': str,                # 视频URL
    'type': str,               # 类型: 'video', 'iframe', 'source', 'platform_link'
    'platform': str,           # 平台: 'youtube', 'vimeo', 'native', 'unknown'
    'video_id': str            # (可选) 视频ID
}
```

---

## 📝 常见问题排查

### Q1: 爬取返回0条结果

**原因**: 网站HTML结构已变化或选择器不匹配

**解决**:
```python
# 1. 打开网站，在浏览器开发者工具 (F12) 中检查HTML结构
# 2. 找到列表项和文章容器的实际CSS class/id
# 3. 更新methods中的选择器

# 例如，如果原选择器是:
news_links = soup.find_all('a', href=re.compile(r'/\d{4}/\d{2}/\d{2}/'))

# 可以改为:
news_links = soup.select('div.article-list a')
```

### Q2: 获取内容为空或太短

**原因**: 正文容器选择器错误或内容被JavaScript动态加载

**解决**:
```python
# 1. 检查 content_selectors 列表是否包含该网站的容器
# 2. 如果网站使用JavaScript，需要使用 Selenium 代替 requests

# 备选选择器列表（按优先级）:
content_selectors = [
    'div.main',
    'article',
    'div[class*="article"]',
    'div[id*="content"]',
    'section.post'
]
```

### Q3: 遇到付费墙或限制

**原因**: 某些网站（如华

盛顿邮报）对爬虫的限制

**解决**:
```python
# 1. 增加访问间隔
time.sleep(3)  # 改为3秒

# 2. 改进User-Agent
self.session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.google.com/',
    'Accept-Language': 'zh-CN,zh;q=0.9'
})

# 3. 检测付费内容并跳过
if 'subscribe' in soup.get_text().lower():
    print("付费内容，跳过")
    return '', datetime.now(), [], []
```

### Q4: 时间解析出错

**原因**: 时间格式差异

**解决**:
```python
from dateutil import parser as date_parser

# 使用 dateutil.parser 可以自动识别多种格式
# 支持: 2026-03-20 10:30, 2026/03/20 10:30, March 20, 2026 等

pub_time = date_parser.parse(time_string)
```

---

## 🚀 性能优化建议

### 1. 并发爬取（使用 threading）

```python
from concurrent.futures import ThreadPoolExecutor

def fetch_all_parallel(self):
    """并发爬取所有网站"""
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(self.fetch_nytimes),
            executor.submit(self.fetch_cctv),
            executor.submit(self.fetch_guancha),
            executor.submit(self.fetch_washingtonpost),
        ]
        
        all_articles = []
        for future in futures:
            all_articles.extend(future.result())
        
        return all_articles
```

### 2. 缓存实现

```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=100)
def _fetch_article_content_cached(self, url):
    """缓存已抓取的文章"""
    url_hash = hashlib.md5(url.encode()).hexdigest()
    cache_key = f"/tmp/news_cache/{url_hash}.json"
    
    # 检查缓存...
    
    return self._fetch_article_content(url)
```

### 3. 重试机制

```python
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session_with_retry(self):
    """创建带自动重试的session"""
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=(500, 502, 503, 504)
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session
```

---

## 📚 相关文件

- 主要爬取逻辑: `news_dashboard/core/html_fetcher.py`
- 数据存储: `news_dashboard/core/storage.py`
- 配置文件: `news_dashboard/config/sources.py`
- 新方法代码: `NEW_SITE_FETCHERS.py`
- HTML分析: `NEWS_SITES_STRUCTURE_ANALYSIS.md`

---

## ✅ 验收清单

完成以下步骤代表集成成功：

- [ ] 新方法已复制到 `html_fetcher.py`
- [ ] `fetch_all_domestic()` 已更新包含新网站
- [ ] 运行 `test_new_sites.py` 每个网站都成功返回≥1条文章
- [ ] 文章包含完整的标题、正文、时间、图片等字段
- [ ] 数据库中新增的新闻正确保存
- [ ] dashboard 前端显示来自新网站的新闻
- [ ] 没有发生异常错误或连接超时

---

版本: 1.0  
更新日期: 2026-03-20  
维护者: AI Assistant
