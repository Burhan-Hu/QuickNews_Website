# 📰 两个新闻网站爬虫分析和实现

## 概览

本项目为你分析和创建了 **Al Jazeera (英文国际新闻)** 和 **环球时报 (中文国际新闻)** 两个网站的爬虫。

### 📦 可用资源

| 资源 | 文件 | 说明 |
|------|------|------|
| **HTML 结构分析** | `WEBSITE_ANALYSIS.md` | 详细的 HTML 结构、CSS/XPath 选择器、代码模板 |
| **爬虫代码** | `news_dashboard/core/aljazeera_fetcher.py` | Al Jazeera 爬虫实现 |
| **爬虫代码** | `news_dashboard/core/globaltimes_fetcher.py` | 环球时报爬虫实现 |
| **测试工具** | `news_dashboard/core/test_fetchers.py` | 爬虫测试和验证工具 |
| **使用指南** | `news_dashboard/FETCHER_GUIDE.md` | 详细的集成和使用文档 |
| **快速参考** | `QUICK_REFERENCE.md` | 选择器、代码片段速查表 |
| **总结** | `CRAWLERS_SUMMARY.md` | 项目总结和下一步行动 |

---

## 🚀 快速开始 (5分钟)

### 1️⃣ 测试爬虫

```bash
# 进入爬虫目录
cd d:\qknews\news_dashboard\core

# 运行测试 (需要 requests 和 beautifulsoup4)
python test_fetchers.py --all

# 或只测试某个爬虫
python test_fetchers.py --aljazeera
python test_fetchers.py --globaltimes
```

### 2️⃣ 在你的代码中使用

```python
from aljazeera_fetcher import AlJazeeraFetcher
from globaltimes_fetcher import GlobalTimesFetcher

# Al Jazeera
aj_fetcher = AlJazeeraFetcher(delay=2.0)
article = aj_fetcher.fetch_article('https://www.aljazeera.com/news/2026/3/19/...')
print(f"标题: {article['title']}")
print(f"作者: {article['author']}")
print(f"时间: {article['publish_date']}")

# 环球时报
gt_fetcher = GlobalTimesFetcher(delay=2.0)
article = gt_fetcher.fetch_article('https://www.globaltimes.cn/page/202603/1357248.shtml')
print(f"标题: {article['title']}")
print(f"内容长度: {len(article['content'])} 字符")
print(f"图片数: {len(article['images'])}")
```

---

## 📊 两个网站对比

### Al Jazeera (英文国际新闻)

**URL 示例**:
```
https://www.aljazeera.com/news/2026/3/19/us-f-35-aircraft-makes-emergency-landing-after-a-combat-mission-over-iran
https://www.aljazeera.com/sports/2026/3/20/japan-vs-australia-womens-asian-cup-final-team-news-start-and-lineups
```

**特点**:
- ✓ 英文新闻，覆盖全球
- ✓ 分类完整 (News, Sports, Features, Opinions, Economy)
- ✓ HTML 结构清晰
- ⚠️ 首页用 React 动态加载 (需要 Selenium 处理)
- ✓ 正文容器: `<article>`
- ✓ 图片 CDN: wp-content

**发布时间格式**: 
```
ISO 8601: 2026-03-19T00:00:00Z
文本格式: 19 Mar 2026
```

### 环球时报 (中文国际新闻)

**URL 示例**:
```
https://www.globaltimes.cn/page/202603/1357248.shtml
https://www.globaltimes.cn/page/202603/1357239.shtml
```

**特点**:
- ✓ 中文新闻，国际视角
- ✓ 纯静态 HTML，易于爬取
- ✓ URL 规律: `/page/YYYYMM/ID.shtml`
- ✓ 多个频道 (国际、中国、观点等)
- ✓ 正文容器: `<article>`
- ✓ 图片 CDN: /Portals/

**发布时间格式**:
```
文本格式: Published: Mar 20, 2026 12:04 AM
```

---

## 🎯 核心选择器

### Al Jazeera

```css
h1                          /* 标题 */
a[href*="/author/"]         /* 作者 */
time                        /* 发布时间 */
article                     /* 正文容器 */
article img                 /* 文章内图片 */
iframe[src*="youtube"]      /* 视频 */
a[href^="/news/"]          /* 列表链接 */
```

### 环球时报

```css
h1                          /* 标题 */
a[href*="/author/"]         /* 作者 */
[class*="date"]            /* 发布时间 */
article                     /* 正文容器 */
img[src*="/Portals/"]      /* CDN 图片 */
iframe[src*="youtube"]      /* 视频 */
a[href*="/page/"]          /* 列表链接 */
```

---

## 📝 返回的数据结构

```python
article = {
    'source': 'Al Jazeera',              # 新闻源
    'url': 'https://...',               # 文章 URL
    'title': '文章标题',                 # 标题
    'author': '作者名称',                # 作者
    'publish_date': '2026-03-19...',     # 发布时间
    'content': '正文内容...',            # 正文
    'images': [                         # 图片列表
        {
            'src': 'https://...',       # 图片 URL
            'alt': '图片说明',          # 替代文本
            'title': '标题'             # 图片标题
        }
    ],
    'videos': [                         # 视频列表
        {
            'src': 'https://...',
            'type': 'iframe'
        }
    ],
    'category': 'news',                 # 分类
    'fetched_at': '2026-03-20T...'      # 爬取时间
}
```

---

## 🔍 主要功能

### Al Jazeera 爬虫

```python
from aljazeera_fetcher import AlJazeeraFetcher

fetcher = AlJazeeraFetcher(delay=2.0)

# 爬取单篇文章
article = fetcher.fetch_article(url)

# 爬取列表 (需要 Selenium 处理 JS)
articles = fetcher.fetch_list(category='news')
# 可选分类: 'news', 'sports', 'features', 'opinions', 'economy'
```

### 环球时报爬虫

```python
from globaltimes_fetcher import GlobalTimesFetcher

fetcher = GlobalTimesFetcher(delay=2.0)

# 爬取单篇文章
article = fetcher.fetch_article(url)

# 爬取列表
articles = fetcher.fetch_list(channel='world')
# 可选频道: 'world', 'china', 'home', 'opinion', 'in-depth'

# 爬取首页推荐
highlights = fetcher.fetch_highlights()

# 解析时间
dt = GlobalTimesFetcher.parse_datetime("Mar 20, 2026 12:04 AM")
```

---

## 📚 文档导航

```
d:\qknews\
├── CRAWLERS_SUMMARY.md          ← 详细总结 (推荐首先阅读)
├── QUICK_REFERENCE.md           ← 速查表 (选择器、代码片段)
├── WEBSITE_ANALYSIS.md          ← 完整的 HTML 分析
└── news_dashboard\
    ├── FETCHER_GUIDE.md         ← 使用和集成指南
    └── core\
        ├── aljazeera_fetcher.py  ← Al Jazeera 爬虫代码
        ├── globaltimes_fetcher.py ← 环球时报爬虫代码
        └── test_fetchers.py      ← 测试工具
```

---

## 🛠️ 依赖安装

```bash
# 基础爬虫需要
pip install requests beautifulsoup4

# 可选: 处理 JavaScript (Al Jazeera 列表)
pip install selenium
# 或
pip install playwright
python -m playwright install

# 可选: 定时任务
pip install APScheduler

# 可选: 数据库存储
pip install pymysql sqlalchemy
```

---

## ⚡ 使用示例

### 例1: 爬取单篇文章

```python
from aljazeera_fetcher import AlJazeeraFetcher

fetcher = AlJazeeraFetcher(delay=2.0)

# Al Jazeera
url = 'https://www.aljazeera.com/news/2026/3/19/us-f-35-aircraft-makes-emergency-landing-after-a-combat-mission-over-iran'
article = fetcher.fetch_article(url)

if 'error' not in article:
    print(f"✓ {article['title']}")
    print(f"  作者: {article['author']}")
    print(f"  时间: {article['publish_date']}")
    print(f"  图片: {len(article['images'])} 张")
    print(f"  内容: {article['content'][:100]}...")
```

### 例2: 批量爬取列表

```python
from globaltimes_fetcher import GlobalTimesFetcher

fetcher = GlobalTimesFetcher(delay=2.0)

# 获取国际新闻列表
articles_list = fetcher.fetch_list(channel='world')

print(f"找到 {len(articles_list)} 篇新闻")

for i, item in enumerate(articles_list[:5], 1):
    print(f"\n{i}. {item['title']}")
    
    # 爬取详情
    article = fetcher.fetch_article(item['url'])
    if 'error' not in article:
        print(f"   ✓ 成功爬取")
        print(f"   作者: {article['author']}")
        print(f"   发布: {article['publish_date']}")
```

### 例3: 保存到 JSON

```python
import json
from aljazeera_fetcher import AlJazeeraFetcher

fetcher = AlJazeeraFetcher()
article = fetcher.fetch_article('https://...')

# 保存为 JSON
with open('article.json', 'w', encoding='utf-8') as f:
    json.dump(article, f, ensure_ascii=False, indent=2)

# 读取
with open('article.json', 'r', encoding='utf-8') as f:
    loaded = json.load(f)
    print(loaded['title'])
```

### 例4: 集成到现有项目

```python
# 修改 news_dashboard/core/fetcher.py
from aljazeera_fetcher import AlJazeeraFetcher
from globaltimes_fetcher import GlobalTimesFetcher

class NewsManager:
    def __init__(self):
        self.aljazeera = AlJazeeraFetcher(delay=2.0)
        self.globaltimes = GlobalTimesFetcher(delay=2.0)
    
    def fetch_latest_news(self):
        """从所有源获取最新新闻"""
        all_news = []
        
        # Al Jazeera
        try:
            aj_list = self.aljazeera.fetch_list('news')
            for item in aj_list[:5]:
                article = self.aljazeera.fetch_article(item['url'])
                if 'error' not in article:
                    all_news.append(article)
        except Exception as e:
            print(f"Al Jazeera 错误: {e}")
        
        # Global Times
        try:
            gt_list = self.globaltimes.fetch_list('world')
            for item in gt_list[:5]:
                article = self.globaltimes.fetch_article(item['url'])
                if 'error' not in article:
                    all_news.append(article)
        except Exception as e:
            print(f"Global Times 错误: {e}")
        
        return all_news

# 使用
manager = NewsManager()
news = manager.fetch_latest_news()
for article in news:
    print(f"- {article['title']} ({article['source']})")
```

---

## 🔴 常见问题

### Q: 爬虫爬不到数据?

**A**: 
1. 检查网络连接
2. 确认 URL 格式正确
3. 查看错误消息 (error 字段)
4. 对于 Al Jazeera 列表，可能需要 Selenium

### Q: 数据中文乱码?

**A**: 环球时报已设置 UTF-8，确保：
- 爬虫: `resp.encoding = 'utf-8'` ✓
- 数据库: `charset='utf8mb4'`
- 文件: 用 UTF-8 编码保存

### Q: 被频繁封IP?

**A**: 
- 增加 delay (延迟): `delay=5.0`
- 使用代理服务
- 限制并发数

### Q: 如何处理 Al Jazeera 的首页列表？

**A**: 首页使用 React 动态加载，建议：
```python
# 方案1: 使用 Selenium
from selenium import webdriver
driver = webdriver.Chrome()
driver.get('https://www.aljazeera.com/news/')
# 等待加载...

# 方案2: 直接爬取分类页
fetcher.fetch_list('news')  # 爬取 /news/ 页面

# 方案3: 使用 API (如果有)
# 在浏览器开发者工具中查看网络请求
```

---

## 📈 性能建议

| 场景 | Delay | Workers | 说明 |
|------|-------|---------|------|
| 单篇爬取 | 2s | 1 | 标准 |
| 批量爬取 | 1s | 3 | 适度并发 |
| 生产环境 | 3-5s | 2 | 稳定安全 |
| 测试 | 0.5s | 1 | 快速验证 |

---

## 🔐 反爬虫防范

爬虫已包含：
- ✓ User-Agent 伪装
- ✓ 请求延迟控制
- ✓ 错误重试机制

建议增加：
- 轮流使用 User-Agent
- 使用代理池
- 设置请求头 (Referer 等)

---

## 📞 获取帮助

1. **快速参考**: 查看 `QUICK_REFERENCE.md` (选择器、代码片段)
2. **详细文档**: 查看 `WEBSITE_ANALYSIS.md` (HTML 结构分析)
3. **集成指南**: 查看 `FETCHER_GUIDE.md` (使用和最佳实践)
4. **测试工具**: 运行 `python test_fetchers.py --all`

---

## 🎯 建议的下一步

1. ✅ 运行 `test_fetchers.py --all` 验证爬虫
2. ✅ 阅读 `QUICK_REFERENCE.md` 快速上手
3. ✅ 查看 `WEBSITE_ANALYSIS.md` 理解 HTML 结构
4. ✅ 集成爬虫到你的项目
5. ✅ 添加数据库存储
6. ✅ (可选) 设置定时任务

---

## 📋 checklist

- [ ] 已安装依赖 (`requests`, `beautifulsoup4`)
- [ ] 已运行 `test_fetchers.py` 验证
- [ ] 已阅读 `QUICK_REFERENCE.md`
- [ ] 已测试单篇文章爬取
- [ ] 已测试列表爬取
- [ ] 已集成到项目
- [ ] 已添加错误处理
- [ ] 已设置日志记录

---

## ⚖️ 法律与道德

请遵守以下原则：
- ✅ 检查 robots.txt
- ✅ 设置合理延迟 (> 1秒)
- ✅ 遵守网站服务条款
- ✅ 不爬取私人信息
- ❌ 不用于商业竞争
- ❌ 不大规模滥用

---

## 版本信息

- **创建日期**: 2026-03-20
- **爬虫版本**: 1.0
- **Python 版本**: 3.6+
- **依赖**: requests, beautifulsoup4

---

## 文件清单

```
d:\qknews\
├── CRAWLERS_SUMMARY.md          ← 项目总结 (推荐先读)
├── QUICK_REFERENCE.md           ← 速查表
├── WEBSITE_ANALYSIS.md          ← HTML 分析
│
└── news_dashboard\
    ├── FETCHER_GUIDE.md         ← 使用指南
    └── core\
        ├── aljazeera_fetcher.py  ← Al Jazeera 爬虫 ⭐
        ├── globaltimes_fetcher.py ← 环球时报爬虫 ⭐
        └── test_fetchers.py      ← 测试工具 ⭐
```

⭐ = 核心文件

---

**现在就开始使用爬虫吧！** 🚀

```bash
cd d:\qknews\news_dashboard\core
python test_fetchers.py --all
```

祝你爬虫之旅愉快！

