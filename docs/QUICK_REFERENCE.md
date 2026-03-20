# 爬虫快速参考卡 (Cheat Sheet)

## 📌 选择器速查

### Al Jazeera

| 元素 | CSS 选择器 | XPath |
|------|----------|-------|
| 标题 | `h1` | `//h1` |
| 作者 | `a[href*="/author/"]` | `//a[contains(@href, '/author/')]` |
| 时间 | `time` | `//time/@datetime` |
| 正文 | `article` | `//article` |
| 图片 | `article img` | `//article//img` |
| 视频 | `iframe[src*="youtube"]` | `//iframe[contains(@src, 'youtube')]` |
| 列表链接 | `a[href^="/news/"]` | `//a[contains(@href, '/news/')]` |

### 环球时报

| 元素 | CSS 选择器 | XPath |
|------|----------|-------|
| 标题 | `h1` | `//h1` |
| 作者 | `a[href*="/author/"]` | `//a[contains(@href, '/author/')]` |
| 时间 | `[class*="date"]` | `//*[contains(@class, 'date')]` |
| 正文 | `article` | `//article` |
| 图片 | `img[src*="/Portals/"]` | `//img[contains(@src, '/Portals/')]` |
| 视频 | `iframe[src*="youtube"]` | `//iframe[contains(@src, 'youtube')]` |
| 列表链接 | `a[href*="/page/"]` | `//a[contains(@href, '/page/')]` |

---

## 🚀 快速代码片段

### Al Jazeera - 爬取单篇

```python
from aljazeera_fetcher import AlJazeeraFetcher

fetcher = AlJazeeraFetcher(delay=2.0)
article = fetcher.fetch_article('https://www.aljazeera.com/news/2026/3/19/...')

print(article['title'])
print(article['author'])
print(article['publish_date'])
print(len(article['images']), "images")
print(article['content'][:200])
```

### Al Jazeera - 爬取列表

```python
articles = fetcher.fetch_list(category='news')
# 返回: [{'title': '...', 'url': '...', 'category': 'news'}, ...]
```

### 环球时报 - 爬取单篇

```python
from globaltimes_fetcher import GlobalTimesFetcher

fetcher = GlobalTimesFetcher(delay=2.0)
article = fetcher.fetch_article('https://www.globaltimes.cn/page/202603/1357248.shtml')

print(article['title'])
print(article['author'])
print(article['publish_date'])
```

### 环球时报 - 爬取列表

```python
articles = fetcher.fetch_list(channel='world')  
# world, china, home, opinion, in-depth
```

### 解析环球时报时间

```python
from globaltimes_fetcher import GlobalTimesFetcher
from datetime import datetime

dt = GlobalTimesFetcher.parse_datetime("Mar 20, 2026 12:04 AM")
print(dt)  # datetime(2026, 3, 20, 0, 4)
```

---

## 📂 文件位置

```
d:\qknews\
├── CRAWLERS_SUMMARY.md                    ← 本文件
├── WEBSITE_ANALYSIS.md                    ← 详细分析
├── news_dashboard\
│   ├── FETCHER_GUIDE.md                   ← 使用指南
│   └── core\
│       ├── aljazeera_fetcher.py           ← Al Jazeera 爬虫
│       ├── globaltimes_fetcher.py         ← 环球时报爬虫
│       └── test_fetchers.py               ← 测试工具
```

---

## 🎯 URL 规律

### Al Jazeera
```
https://www.aljazeera.com/{category}/{year}/{month}/{day}/{slug-title}

示例:
https://www.aljazeera.com/news/2026/3/19/us-f-35-aircraft-makes-emergency-landing-...
https://www.aljazeera.com/sports/2026/3/20/japan-vs-australia-...
```

### 环球时报
```
https://www.globaltimes.cn/page/{YYYYMM}/{article_id}.shtml

示例:
https://www.globaltimes.cn/page/202603/1357248.shtml
https://www.globaltimes.cn/page/202603/1357239.shtml
```

---

## 🔗 频道/分类 URL

### Al Jazeera
- News: https://www.aljazeera.com/news/
- Sports: https://www.aljazeera.com/sports/
- Features: https://www.aljazeera.com/features/
- Opinions: https://www.aljazeera.com/opinions/
- Economy: https://www.aljazeera.com/economy/

### 环球时报
- 首页: https://www.globaltimes.cn/index.html
- 国际 ⭐: https://www.globaltimes.cn/world/index.html
- 中国: https://www.globaltimes.cn/china/index.html
- 观点: https://www.globaltimes.cn/opinion/index.html
- 深度: https://www.globaltimes.cn/In-depth/index.html

---

## 📊 返回数据结构

```python
{
    'source': 'Al Jazeera',           # 或 'Global Times'
    'url': 'https://...',
    'title': '文章标题',
    'author': '作者名称',
    'publish_date': '2026-03-19...',  # ISO 格式 或 "Mar 20, 2026 12:04 AM"
    'content': '正文...',
    'images': [                       # 图片列表
        {
            'src': 'https://...',
            'alt': '图片说明',
            'title': '标题'
        }
    ],
    'videos': [                       # 视频列表
        {
            'src': 'https://www.youtube.com/embed/...',
            'type': 'iframe'
        }
    ],
    'category': 'news',
    'fetched_at': '2026-03-20T12:34:56.789123'
}
```

---

## ⚙️ 初始化参数

```python
# 所有爬虫通用
fetcher = AlJazeeraFetcher(delay=2.0)  # delay: 请求间隔(秒)
fetch_article(url)                      # 爬取单篇
fetch_list(category/channel)            # 爬取列表
```

---

## 🐛 常见错误和解决

| 错误 | 原因 | 解决 |
|------|------|------|
| `requests.ConnectionError` | 网络问题 | 检查网络连接 |
| `requests.Timeout` | 请求超时 | 增加延迟: `delay=5.0` |
| 页面空白/列表为空 | JS 动态加载 | 使用 Selenium (Al Jazeera) |
| 图片404 | CDN 问题或 Referer | 添加 Referer 请求头 |
| 中文乱码 | 编码问题 | 已修复，确认数据库 UTF-8 |
| 被频繁封IP | 爬取过快 | 增加 delay，使用代理 |

---

## 🧪 快速测试

```bash
# 进入爬虫目录
cd d:\qknews\news_dashboard\core

# 测试所有爬虫
python test_fetchers.py --all

# 只测试 Al Jazeera
python test_fetchers.py --aljazeera

# 只测试环球时报
python test_fetchers.py --globaltimes

# 导出示例数据到 JSON
python test_fetchers.py --export
```

---

## 💡 最佳实践

```python
# ✅ 正确
fetcher = AlJazeeraFetcher(delay=2.0)    # 设置延迟
article = fetcher.fetch_article(url)     # 使用爬虫实例
if 'error' not in article:               # 检查错误
    db.save(article)

# ❌ 错误
requests.get(url)                        # 直接 requests
soup.select_one('article')               # 没有错误处理
time.sleep(0.1)                          # 延迟太短，易被封
```

---

## 🔐 反爬虫防范

已在爬虫代码中实现：

```python
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)...'
}
```

建议增加：

```python
import time
import random

# 添加随机延迟
delay = random.uniform(2.0, 4.0)
time.sleep(delay)

# 轮流使用 User-Agent
USER_AGENTS = ['Mozilla/5.0...', 'Chrome/...', ...]
headers['User-Agent'] = random.choice(USER_AGENTS)

# 使用代理 (可选)
proxies = {'https': 'http://proxy:port'}
requests.get(url, proxies=proxies)
```

---

## 📈 性能建议

| 场景 | 延迟 | Worker | 说明 |
|------|------|--------|------|
| 单篇爬取 | 2秒 | 1 | 标准速度 |
| 批量爬取 | 1秒 | 3 | 适度并发 |
| 生产环境 | 3-5秒 | 2 | 保险起见 |
| 测试环境 | 0.5秒 | 1 | 仅用于测试 |

---

## 📌 常用 Regex

```python
import re

# 提取发布时间 (环球时报)
date_text = "Published: Mar 20, 2026 12:04 AM"
match = re.search(r'Published:\s*(.+?)(?:\n|$)', date_text)
date_str = match.group(1)

# 提取作者 (环球时报)
author_text = "By Hu Yuwei and Liang Rui"
authors = re.findall(r'(?:By\s+|and\s+)(\w+\s+\w+)', author_text)

# 提取 YouTube ID
youtube_url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
video_id = youtube_url.split('/')[-1]

# 提取文章ID (环球时报)
article_url = "https://www.globaltimes.cn/page/202603/1357248.shtml"
article_id = re.search(r'/(\d+)\.shtml', article_url).group(1)
```

---

## 🔄 处理错误和重试

```python
import time

def fetch_with_retry(url, max_retries=3, delay=2.0):
    fetcher = AlJazeeraFetcher(delay=delay)
    
    for attempt in range(max_retries):
        try:
            return fetcher.fetch_article(url)
        except Exception as e:
            if attempt < max_retries - 1:
                wait = (2 ** attempt) * delay  # 指数退避
                print(f"重试 {attempt + 1}/{max_retries - 1}，等待 {wait}s...")
                time.sleep(wait)
            else:
                print(f"失败: {e}")
                return {'error': str(e)}
```

---

## 💾 保存到文件

```python
import json

article = fetcher.fetch_article(url)

# 保存为 JSON
with open('article.json', 'w', encoding='utf-8') as f:
    json.dump(article, f, ensure_ascii=False, indent=2)

# 保存为 CSV (简单格式)
import csv
with open('articles.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Title', 'Author', 'Date', 'Source'])
    writer.writerow([article['title'], article['author'], article['publish_date'], article['source']])

# 保存为 Markdown
with open('article.md', 'w', encoding='utf-8') as f:
    f.write(f"# {article['title']}\n\n")
    f.write(f"**作者**: {article['author']}\n")
    f.write(f"**时间**: {article['publish_date']}\n")
    f.write(f"**来源**: {article['source']}\n\n")
    f.write(f"## 正文\n\n{article['content']}\n")
```

---

## 🗂️ BeautifulSoup 常用方法

```python
from bs4 import BeautifulSoup

soup = BeautifulSoup(html, 'html.parser')

# 查找单个元素
elem = soup.select_one('h1')              # CSS 选择器 (返回第一个)
elem = soup.find('h1')                    # HTML 标签

# 查找多个元素
elems = soup.select('article img')        # CSS 选择器 (返回列表)
elems = soup.find_all('img')              # HTML 标签

# 获取文本
text = elem.get_text(strip=True)

# 获取属性
href = elem.get('href', '')               # 默认值: ''
src = elem['src']                         # 直接访问

# 父元素
parent = elem.parent

# 遍历
for child in elem.children:
    print(child)
```

---

## 📞 支持文档

| 文档 | 位置 | 用途 |
|------|------|------|
| 完整分析 | `WEBSITE_ANALYSIS.md` | HTML 结构、代码模板 |
| 使用指南 | `FETCHER_GUIDE.md` | 集成、配置、最佳实践 |
| 本文 | `CRAWLERS_SUMMARY.md` | 快速参考 |
| 测试工具 | `test_fetchers.py` | 验证爬虫功能 |

---

**最后更新**: 2026-03-20  
**版本**: 1.0  
**难度**: ⭐⭐ (初中级)

---

## 👉 立即开始

```bash
# 1. 进入目录
cd d:\qknews\news_dashboard\core

# 2. 运行测试
python test_fetchers.py --all

# 3. 查看输出 - 应该看到成功的爬取结果

# 4. 开始使用爬虫
python

# 5. Python REPL 中
from aljazeera_fetcher import AlJazeeraFetcher
fetcher = AlJazeeraFetcher()
article = fetcher.fetch_article('https://www.aljazeera.com/news/2026/3/19/...')
print(article['title'])
```

开始爬虫之旅吧！🚀

