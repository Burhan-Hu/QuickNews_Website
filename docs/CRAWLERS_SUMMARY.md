# 网站HTML结构分析总结

> 分析时间: 2026-03-20  
> 分析对象: Al Jazeera (英文国际新闻) 和 环球时报 (中文国际新闻)

---

## 一、快速对比表

| 特性 | Al Jazeera | 环球时报 |
|------|-----------|--------|
| **主URL** | https://www.aljazeera.com/ | https://www.globaltimes.cn/ |
| **文章URL格式** | `/news/YYYY/M/D/slug` | `/page/YYYYMM/ID.shtml` |
| **动态加载** | ✓ React | ✗ 静态 |
| **爬虫难度** | 中等-难 | 简单 |
| **字符编码** | UTF-8 英文 | UTF-8 中文 |
| **正文容器** | `<article>` | `<article>` |
| **发布时间格式** | ISO 8601 或文本 | "Mar 20, 2026 12:04 AM" |
| **图片CDN** | wp-content | /Portals/ |
| **视频方式** | YouTube iframe | YouTube/优酷 iframe |

---

## 二、详细选择器列表

### 📍 Al Jazeera 选择器

#### 列表页选择器
```
最高效: a[href^="/news/"], a[href^="/sports/"]
备选:   h2 a, h3 a, [class*="article-title"] a
最佳实践: 用 XPath: //a[contains(@href, '/2026/')]  (过滤年份)
```

#### 详情页选择器
```
标题:    h1                          或  article h1
作者:    a[href*="/author/"]          或  span:contains("By")
时间:    time                        (datetime 属性)
正文:    article                     或  [class*="article-body"]
图片:    article img                 或  img[src*="wp-content"]
视频:    iframe[src*="youtube"]
```

### 📍 环球时报选择器

#### 列表页选择器
```
最高效: a[href*="/page/"]  (过滤: 含 /page/ 和 /2026/)
XPath: //a[contains(@href, '/page/')]
注意: 过滤很短的文本 (len > 10) 避免widget
```

#### 详情页选择器
```
标题:    h1                          或  [class*="article-title"]
作者:    a[href*="/author/"]          或  (在时间elem中查找 "By ")
时间:    span:contains("Published:")   (正则提取)
正文:    article                     或  [class*="article-content"]
图片:    img[src*="/Portals/"]       或  article img
视频:    iframe[src*="youtube"]  或  iframe[src*="youku"]
```

---

## 三、示例文章URL

### Al Jazeera 示例 (6篇)
1. https://www.aljazeera.com/news/2026/3/19/us-f-35-aircraft-makes-emergency-landing-after-a-combat-mission-over-iran
2. https://www.aljazeera.com/news/2026/3/19/mexican-military-says-11-killed-in-raid-targeting-sinaloa-cartel-leader
3. https://www.aljazeera.com/news/2026/3/19/death-toll-surpasses-1-000-in-lebanon-as-israeli-bombardment-continues
4. https://www.aljazeera.com/sports/2026/3/20/japan-vs-australia-womens-asian-cup-final-team-news-start-and-lineups
5. https://www.aljazeera.com/features/2026/3/18/in-cape-towns-historic-bo-kaap-homes-under-siege-from-rich-foreign-buyers
6. https://www.aljazeera.com/opinions/2026/3/20/eid-under-siege-little-to-celebrate-in-gaza-as-israel-tightens-chokehold

**分类URL**: 
- News: https://www.aljazeera.com/news/
- Sports: https://www.aljazeera.com/sports/
- Features: https://www.aljazeera.com/features/
- Opinions: https://www.aljazeera.com/opinions/

### 环球时报示例 (6篇)
1. https://www.globaltimes.cn/page/202603/1357248.shtml
2. https://www.globaltimes.cn/page/202603/1357239.shtml
3. https://www.globaltimes.cn/page/202603/1357255.shtml
4. https://www.globaltimes.cn/page/202603/1357256.shtml
5. https://www.globaltimes.cn/page/202603/1357236.shtml
6. https://www.globaltimes.cn/page/202603/1357217.shtml

**频道URL**:
- 首页: https://www.globaltimes.cn/index.html
- 国际: https://www.globaltimes.cn/world/index.html ⭐ (推荐)
- 中国: https://www.globaltimes.cn/china/index.html
- 观点: https://www.globaltimes.cn/opinion/index.html
- 深度: https://www.globaltimes.cn/In-depth/index.html

---

## 四、HTML结构详解

### Al Jazeera 正文HTML示例
```html
<article>
  <h1>US F-35 aircraft makes emergency landing after a combat mission over Iran</h1>
  
  <time datetime="2026-03-19T...Z">19 Mar 2026</time>
  
  <a href="/author/elizabeth_melimopoulos_2012611142024203731">
    Elizabeth Melimopoulos
  </a>
  and Reuters
  
  <div class="article-body">
    <p>An F-35 fighter jet from the United States has made an emergency landing...</p>
    <p>The aircraft landed safely on Thursday...</p>
    
    <figure>
      <img src="https://www.aljazeera.com/wp-content/uploads/2026/03/...jpg" 
           alt="U.S. Air Force F-35 Lightning IIs fly side by side..."
           title="Fighter Jets"/>
      <figcaption>Image caption here</figcaption>
    </figure>
    
    <p>Additional paragraph...</p>
    
    <iframe src="https://www.youtube.com/embed/VIDEO_ID" 
            width="100%" height="400"></iframe>
  </div>
</article>
```

### 环球时报 正文HTML示例
```html
<article>
  <h1>Local officials' holistic perspective 'cannot be separated from CPC's efficient central policy implementation system': former Belgian ambassador</h1>
  
  <div>
    By <a href="/author/Reporter-Hu-Yuwei">Hu Yuwei</a> and Liang Rui<br/>
    Published: Mar 20, 2026 12:04 AM
  </div>
  
  <div class="article-content">
    <p>Editor's Note: Chinese President Xi Jinping has pointed out...</p>
    
    <figure>
      <img src="https://www.globaltimes.cn/Portals/0/attachment/2026/2026-03-19/f22e5b7f-9c2c-4803-afc7-d7be177ae493.jpeg"
           alt="The rural landscape of Dongchuan in Kunming"/>
      <figcaption>The rural landscape of Dongchuan in Kunming, Southwest China's Yunnan Province Photo: VCG</figcaption>
    </figure>
    
    <p>In the rugged hills of Kunming's Dongchuan district...</p>
    
    <iframe src="https://www.youtube.com/embed/..." width="100%" height="400"></iframe>
  </div>
</article>
```

---

## 五、数据提取规则

### 时间格式处理

**Al Jazeera**:
```python
# datetime 属性（首选）
time_elem = soup.find('time')
publish_date = time_elem.get('datetime')
# 结果: "2026-03-19T00:00:00Z"

# 文本内容（备选）
text = time_elem.text
# 结果: "19 Mar 2026"
```

**环球时报**:
```python
# 查找包含 "Published:" 的元素
import re
text = "Published: Mar 20, 2026 12:04 AM"
match = re.search(r'Published:\s*(.+?)(?:\n|$)', text)
publish_date = match.group(1)  # "Mar 20, 2026 12:04 AM"

# Python 时间解析
from datetime import datetime
dt = datetime.strptime("Mar 20, 2026 12:04 AM", '%b %d, %Y %I:%M %p')
# dt: datetime(2026, 3, 20, 0, 4)
```

### 图片处理

**Al Jazeera**:
```python
img_url = "https://www.aljazeera.com/wp-content/uploads/2026/03/xxxx.jpg"
# 特点: wp-content 路径，高质量
# 可添加参数: ?resize=1200x800&quality=80
```

**环球时报**:
```python
img_url = "https://www.globaltimes.cn/Portals/0/attachment/2026/2026-03-19/uuid.jpeg"
# 特点: /Portals/ 路径，UUID 命名
# 可能需要设置 Referer header
```

### 视频处理

**两个网站都使用 iframe 嵌入**:
```html
<!-- YouTube -->
<iframe src="https://www.youtube.com/embed/VIDEO_ID" width="100%" height="400"></iframe>

<!-- 优酷 (仅环球时报) -->
<iframe src="https://player.youku.com/embed/..." width="100%" height="400"></iframe>
```

提取方法:
```python
for iframe in soup.select('iframe'):
    video_src = iframe.get('src')
    if 'youtube' in video_src:
        video_id = video_src.split('/embed/')[-1]
    elif 'youku' in video_src:
        # 优酷ID提取
        pass
```

---

## 六、爬虫推荐方案

### 简易版 (BeautifulSoup)
```python
# ✅ 适合: 爬取单篇文章、定点爬取
# ✅ 优点: 快速、简单、依赖少
# ❌ 缺点: 无法处理 JS 动态加载 (Al Jazeera 列表)

requests + BeautifulSoup
```

### 标准版 (已提供)
```python
# ✅ 包含: AlJazeeraFetcher, GlobalTimesFetcher 类
# ✅ 支持: 单篇爬取、列表爬取、错误处理
# ❌ 仍需: Selenium/Playwright 处理 AJ 首页 JS

# 文件: news_dashboard/core/aljazeera_fetcher.py
#      news_dashboard/core/globaltimes_fetcher.py
```

### 完整版 (生产环境)
```python
# ✅ 添加内容: 
#   - Selenium/Playwright 处理 JS
#   - 数据库存储
#   - 定时任务 (APScheduler)
#   - 日志记录
#   - 错误重试和失败恢复
#   - 代理轮转
#   - 缓存策略

# 需要额外安装:
# - selenium / playwright
# - APScheduler
# - sqlalchemy
```

---

## 七、常见陷阱

| 陷阱 | 原因 | 解决方案 |
|------|------|---------|
| **Al Jazeera 列表为空** | 首页用 React 动态加载 | 使用 Selenium/Playwright 或直接爬分类页 |
| **图片404错误** | CDN 需要 Referer | 添加请求头: `'Referer': 'https://www.aljazeera.com'` |
| **环球时报乱码** | 未设置编码 | `resp.encoding = 'utf-8'` |
| **被频繁封IP** | 请求过快 | 增加 delay (延迟) 到 3-5 秒 |
| **视频src为空** | iframe 加载延迟 | 检查是否需要等待 JS 加载 |
| **时间解析失败** | 格式不一致 | 多尝试几种日期格式 |
| **作者信息缺失** | HTML 结构变化 | 添加备选选择器和正则匹配 |

---

## 八、下一步行动

### 立即可用的文件

1. **分析文档**: [`d:\qknews\WEBSITE_ANALYSIS.md`](../WEBSITE_ANALYSIS.md)
   - 完整的 HTML 结构分析
   - CSS 和 XPath 选择器
   - BeautifulSoup 代码模板

2. **爬虫代码**: 
   - [`d:\qknews\news_dashboard\core\aljazeera_fetcher.py`](../core/aljazeera_fetcher.py)
   - [`d:\qknews\news_dashboard\core\globaltimes_fetcher.py`](../core/globaltimes_fetcher.py)

3. **测试工具**: [`d:\qknews\news_dashboard\core\test_fetchers.py`](../core/test_fetchers.py)
   ```bash
   cd d:\qknews\news_dashboard\core
   python test_fetchers.py --all
   ```

4. **使用指南**: [`d:\qknews\news_dashboard\FETCHER_GUIDE.md`](./FETCHER_GUIDE.md)

### 集成步骤

1. **测试爬虫** (1-2 分钟)
   ```bash
   python test_fetchers.py --all
   ```

2. **导入模块** (30 秒)
   ```python
   from aljazeera_fetcher import AlJazeeraFetcher
   from globaltimes_fetcher import GlobalTimesFetcher
   ```

3. **爬取数据** (1 分钟/篇)
   ```python
   fetcher = AlJazeeraFetcher()
   article = fetcher.fetch_article('https://...')
   ```

4. **存储数据** (根据你的 DB 配置)
   ```python
   # 存储到数据库或文件
   ```

5. **定时更新** (可选)
   ```python
   from apscheduler.schedulers.background import BackgroundScheduler
   # 每小时检查一次新闻
   ```

---

## 九、支持和反馈

### 问题排查清单

- [ ] 爬虫已安装依赖 (`requests`, `beautifulsoup4`)
- [ ] 网络连接正常，可访问两个网站
- [ ] 已尝试单个 URL 测试
- [ ] 已检查 User-Agent 和 Referer 头
- [ ] 已检查字符编码 (UTF-8)
- [ ] 已查看日志/控制台输出

### 获取帮助

1. 查看本文档中的 "常见陷阱"
2. 查看 `FETCHER_GUIDE.md` 的常见问题部分
3. 检查 `test_fetchers.py` 输出和错误信息
4. 使用浏览器开发者工具检查实际 HTML 结构

---

## 十、工作流总结

```
┌─────────────────────────────────────┐
│ 1. 分析网站 HTML 结构                 │  ✓ 已完成
│    WEBSITE_ANALYSIS.md               │
└─────────────────────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 2. 创建爬虫模块                       │  ✓ 已完成
│    *_fetcher.py                      │
└─────────────────────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 3. 测试爬虫                          │  👈 现在执行
│    python test_fetchers.py --all     │
└─────────────────────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 4. 集成到项目                        │  📋 按需执行
│    修改 fetcher.py / storage.py      │
└─────────────────────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 5. 部署和监控                        │  📊 生产环境
│    定时任务、日志、告警               │
└─────────────────────────────────────┘
```

---

**分析完成 ✓**

现在你已拥有：
- ✅ 详细的 HTML 结构分析
- ✅ 可用的爬虫代码
- ✅ 测试工具和使用指南
- ✅ 故障排除文档

**建议下一步**: 运行 `python test_fetchers.py --all` 来验证爬虫功能。

