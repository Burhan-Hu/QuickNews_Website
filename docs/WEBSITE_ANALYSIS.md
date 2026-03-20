# 新闻爬虫HTML结构分析

## 网站1: Al Jazeera (英文国际新闻)

### 基础信息
- **主页URL**: https://www.aljazeera.com/
- **首页新闻列表**: 动态渲染，使用React框架
- **新闻频道**:
  - 新闻: https://www.aljazeera.com/news/
  - 体育: https://www.aljazeera.com/sports/
  - 特稿: https://www.aljazeera.com/features/
  - 观点: https://www.aljazeera.com/opinions/
  - 经济: https://www.aljazeera.com/economy/

### 新闻文章URL规律
```
https://www.aljazeera.com/{category}/{year}/{month}/{day}/{slug-title}
```
**示例文章**:
- https://www.aljazeera.com/news/2026/3/19/us-f-35-aircraft-makes-emergency-landing-after-a-combat-mission-over-iran
- https://www.aljazeera.com/sports/2026/3/20/japan-vs-australia-womens-asian-cup-final-team-news-start-and-lineups
- https://www.aljazeera.com/features/2026/3/20/why-pakistani-farmers-are-suing-two-german-companies-for-deadly-2022-floods

### 列表页新闻抽取

#### 方案A: 使用CSS选择器（适用于首页和分类页）

**获取新闻链接**:
```css
/* 新闻链接 */
a[href*="/news/"], 
a[href*="/sports/"], 
a[href*="/features/"],
a[href*="/opinions/"]

/* 或更通用的选择 */
article a[href^="/news/"],
div[class*="article"] a[href^="/"],
h2 a[href^="/"],
h3 a[href^="/"]
```

**获取新闻标题**:
```css
h2, h3, a[href^="/news"]
/* 标题通常在 <h2> 或 <h3> 中，或作为 <a> 的文本内容 */
```

**获取新闻摘要/描述**:
```css
p:first-of-type,
[class*="summary"],
[class*="excerpt"],
[class*="description"]
```

**获取发布时间**:
```css
time,
[class*="date"],
[class*="publish"],
span[class*="time"]
```

**获取缩略图**:
```css
img[src*="wp-content"],
img[class*="thumb"],
img[class*="featured"],
picture img
```

### 详情页内容抽取

#### 正文容器选择器:
```css
/* 主要内容容器 */
article,
[class*="article-body"],
[class*="content-body"],
main,
[class*="story-body"]
```

#### 标题选择器:
```css
h1,
article h1,
[class*="article-title"]
```

#### 发布时间选择器:
```css
time,
[class*="publish-date"],
[class*="date-publish"],
span:contains("Published")
```

**时间格式**: `Published On 19 Mar 2026` 或 `19 Mar 2026`

#### 作者选择器:
```css
[class*="author"],
[class*="by-line"],
a[href*="/author/"],
span:contains("By")
```

**作者格式**: `By Elizabeth Melimopoulos and Reuters`

#### 图片选择器:
```css
article img,
[class*="article-body"] img,
img[src*="wp-content/uploads"],
figure img
```

**图片URL格式**: `https://www.aljazeera.com/wp-content/uploads/{year}/{month}/{filename}`

**img标签属性**:
- `src`: 图片URL
- `alt`: 图片说明（通常包含图片描述）
- `title`: 图片标题

#### 图片说明/Caption:
```css
figcaption,
[class*="caption"],
img + p,
[class*="image-caption"]
```

#### 视频元素选择器:
```css
iframe[src*="youtube"],
iframe[src*="player"],
video,
[class*="video-container"],
[class*="embed"]
```

**视频来源**:
- YouTube嵌入: `<iframe src="https://www.youtube.com/embed/..."></iframe>`
- 自托管video: `<video src="..."></video>`
- 其他平台iframe

### XPath 选择器
```xpath
/* 新闻链接 */
//a[contains(@href, '/news/') or contains(@href, '/sports/')]

/* 标题 */
//article//h1 | //h2[@class*='article-title']

/* 发布时间 */
//time/@datetime | //span[contains(text(), 'Published')]

/* 作者 */
//a[contains(@href, '/author/')] | //*[contains(text(), 'By')]

/* 正文 */
//article | //*[@class*='article-body']

/* 图片 */
//article//img | //figure//img
```

---

## 网站2: Global Times (环球时报 - 中文国际新闻)

### 基础信息
- **主页URL**: https://www.globaltimes.cn/
- **国际频道**: https://www.globaltimes.cn/world/index.html
- **频道列表**:
  - 首页: https://www.globaltimes.cn/index.html
  - 中国: https://www.globaltimes.cn/china/index.html
  - 国际: https://www.globaltimes.cn/world/index.html
  - 观点: https://www.globaltimes.cn/opinion/index.html
  - 深度: https://www.globaltimes.cn/In-depth/index.html
  - 生活: https://www.globaltimes.cn/life/index.html

### 新闻文章URL规律
```
https://www.globaltimes.cn/page/{YYYYMM}/{article_id}.shtml
```
**示例文章**:
- https://www.globaltimes.cn/page/202603/1357248.shtml (Mar 20, 2026)
- https://www.globaltimes.cn/page/202603/1357239.shtml (Mar 20, 2026)
- https://www.globaltimes.cn/page/202603/1357255.shtml (Mar 20, 2026)

**URL解析**:
- `202603` = 2026年3月
- `1357248` = 文章ID（递增）

### 列表页新闻抽取

#### CSS选择器方案:

**获取新闻容器**:
```css
/* 新闻列表的容器 */
.news-list,
[class*="news-item"],
[class*="article-item"],
li,
div[class*="article"]

/* 或找到所有的文章链接容器 */
a[href*="/page/"]
```

**获取新闻链接**:
```css
a[href*="/page/"],
a[href^="/page/"],
h2 a,
h3 a,
[class*="article-title"] a
```

**获取标题**:
```css
/* 标题通常在 <a> 标签的文本内或在 <h2>/<h3> 中 */
a[href*="/page/"],
h2, h3
```

**获取发布时间**:
```css
[class*="date"],
[class*="time"],
span[class*="publish"],
time
```

**发布时间格式**: `Mar 20, 2026 12:04 AM`

**获取作者**:
```css
[class*="author"],
a[href*="/author/"],
span:contains("By")
```

**作者格式**: `By Hu Yuwei and Liang Rui`

**获取缩略图**:
```css
img:not([src*="icon"]):not([src*="logo"]),
img[src*="/Portals/"],
figure img
```

### 详情页内容抽取

#### 正文容器选择器:
```css
/* 主要内容区域 */
article,
[class*="article-content"],
[class*="story-body"],
[class*="content-main"],
main
```

#### 标题选择器:
```css
h1,
[class*="article-title"]
```

#### 发布时间选择器:
```css
[class*="date"],
span:contains("Published:"),
time
```

**完全时间格式**: `Published: Mar 20, 2026 12:04 AM`

**时间提取正则**:
```regex
Published:\s*(.+?)(?:\n|$)
# 结果: Mar 20, 2026 12:04 AM
```

#### 作者信息选择器:
```css
[class*="author"],
a[href*="/author/"],
span:contains("By")
```

**作者HTML示例**:
```html
By <a href="/author/Reporter-Name">Name</a>
```

#### 图片选择器:
```css
article img,
[class*="article-content"] img,
img[src*="/Portals/"],
figure img
```

**图片URL格式**: 
- `https://www.globaltimes.cn/Portals/0/attachment/{YYYY}/{YYYY-MM-DD}/{uuid}.jpeg`
- 示例: `https://www.globaltimes.cn/Portals/0/attachment/2026/2026-03-19/f22e5b7f-9c2c-4803-afc7-d7be177ae493.jpeg`

**img标签属性**:
- `src`: 图片URL
- `alt`: 图片说明
- `title`: 可选的标题

#### 图片说明/Caption:
```css
figcaption,
img + p,
[class*="caption"],
[class*="img-description"]
```

**HTML结构示例**:
```html
![Image url](png)
Photo: VCG
<!-- 或 -->
<img src="..." alt="description" />
<p>Photo: VCG</p>
```

#### 视频元素选择器:
```css
[class*="video"],
iframe[src*="youtube"],
iframe[src*="youku"],
iframe[src*="tencent"],
[class*="embed"],
video
```

**视频来源**:
- YouTube: `<iframe src="https://www.youtube.com/embed/..."></iframe>`
- 本地视频: `<video src="..."></video>`
- 中国视频网站: 优酷、腾讯视频等

### XPath 选择器
```xpath
/* 新闻链接 */
//a[contains(@href, '/page/')]

/* 标题 */
//article//h1 | //h2[contains(@class, 'article-title')]

/* 发布时间 */
//span[contains(text(), 'Published:')] | //time/@datetime

/* 作者 */
//a[contains(@href, '/author/')] | //*[contains(text(), 'By')]

/* 正文 */
//article | //*[@class*='article-content']

/* 图片 */
//article//img | //figure//img[contains(@src, '/Portals/')]

/* 视频 */
//iframe[contains(@src, 'youtube')] | //video | //iframe[contains(@src, 'youku')]
```

---

## 爬虫候选URL列表

### Al Jazeera 示例文章:
1. https://www.aljazeera.com/news/2026/3/19/mexican-military-says-11-killed-in-raid-targeting-sinaloa-cartel-leader
2. https://www.aljazeera.com/news/2026/3/19/death-toll-surpasses-1-000-in-lebanon-as-israeli-bombardment-continues
3. https://www.aljazeera.com/sports/2026/3/20/japan-vs-australia-womens-asian-cup-final-team-news-start-and-lineups
4. https://www.aljazeera.com/features/2026/3/18/in-cape-towns-historic-bo-kaap-homes-under-siege-from-rich-foreign-buyers
5. https://www.aljazeera.com/opinions/2026/3/20/eid-under-siege-little-to-celebrate-in-gaza-as-israel-tightens-chokehold
6. https://www.aljazeera.com/economy/2026/3/19/why-are-irans-south-pars-gasfield-qatars-ras-laffan-so-significant

### Global Times 示例文章:
1. https://www.globaltimes.cn/page/202603/1357248.shtml
2. https://www.globaltimes.cn/page/202603/1357239.shtml
3. https://www.globaltimes.cn/page/202603/1357255.shtml
4. https://www.globaltimes.cn/page/202603/1357256.shtml
5. https://www.globaltimes.cn/page/202603/1357236.shtml
6. https://www.globaltimes.cn/page/202603/1357217.shtml

---

## BeautifulSoup 爬虫代码模板

### Al Jazeera 爬虫示例:
```python
from bs4 import BeautifulSoup
import requests
from datetime import datetime

def fetch_aljazeera_article(url):
    """爬取 Al Jazeera 新闻文章"""
    resp = requests.get(url)
    soup = BeautifulSoup(resp.content, 'html.parser')
    
    article = {
        'title': None,
        'author': None,
        'publish_date': None,
        'content': None,
        'images': [],
        'videos': [],
        'source_url': url
    }
    
    # 提取标题
    title_elem = soup.select_one('h1')
    if title_elem:
        article['title'] = title_elem.get_text(strip=True)
    
    # 提取发布时间和作者
    time_elem = soup.select_one('time')
    author_elems = soup.select('a[href*="/author/"]')
    
    if time_elem and time_elem.get('datetime'):
        article['publish_date'] = time_elem.get('datetime')
    
    articles_authors = [a.get_text(strip=True) for a in author_elems]
    if articles_authors:
        article['author'] = ' and '.join(articles_authors)
    
    # 提取正文
    content_elem = soup.select_one('article') or soup.select_one('[class*="article-body"]')
    if content_elem:
        # 移除脚本、样式和不必要的元素
        for tag in content_elem.select('script, style'):
            tag.decompose()
        article['content'] = content_elem.get_text(strip=True)
    
    # 提取图片
    for img in soup.select('article img, [class*="article-body"] img'):
        img_data = {
            'src': img.get('src', ''),
            'alt': img.get('alt', ''),
            'title': img.get('title', '')
        }
        if img_data['src']:
            article['images'].append(img_data)
    
    # 提取视频
    for iframe in soup.select('iframe[src*="youtube"], iframe[src*="player"]'):
        article['videos'].append({
            'src': iframe.get('src', ''),
            'type': 'iframe'
        })
    
    return article


def fetch_aljazeera_list(category='news'):
    """爬取 Al Jazeera 新闻列表"""
    url = f'https://www.aljazeera.com/{category}/'
    # 注意：Al Jazeera 使用 React，可能需要 Selenium 或其他工具处理 JavaScript
    resp = requests.get(url)
    soup = BeautifulSoup(resp.content, 'html.parser')
    
    articles = []
    
    # 查找所有新闻链接
    for link in soup.select('a[href^="/news/"], a[href^="/sports/"]'):
        href = link.get('href')
        if href and href.startswith('http'):
            text = link.get_text(strip=True)
            if text:
                articles.append({
                    'title': text,
                    'url': href
                })
    
    return articles
```

### Global Times 爬虫示例:
```python
from bs4 import BeautifulSoup
import requests
import re
from datetime import datetime

def fetch_globaltimes_article(url):
    """爬取环球时报新闻文章"""
    resp = requests.get(url)
    resp.encoding = 'utf-8'  # 环球时报使用 UTF-8
    soup = BeautifulSoup(resp.content, 'html.parser')
    
    article = {
        'title': None,
        'author': None,
        'publish_date': None,
        'content': None,
        'images': [],
        'videos': [],
        'source_url': url
    }
    
    # 提取标题
    title_elem = soup.select_one('h1')
    if not title_elem:
        title_elem = soup.select_one('[class*="article-title"]')
    if title_elem:
        article['title'] = title_elem.get_text(strip=True)
    
    # 提取发布时间
    # 格式: "Published: Mar 20, 2026 12:04 AM"
    date_text = None
    for elem in soup.select('[class*="date"], span'):
        text = elem.get_text(strip=True)
        if 'Published:' in text:
            date_text = text
            break
    
    if date_text:
        # 提取时间部分：Mar 20, 2026 12:04 AM
        match = re.search(r'Published:\s*(.+?)(?:\n|$)', date_text)
        if match:
            article['publish_date'] = match.group(1).strip()
    
    # 提取作者
    author_text = None
    for elem in soup.select('[class*="author"], a[href*="/author/"]'):
        text = elem.get_text(strip=True)
        if text and not text.startswith('http'):
            author_text = text
            break
    
    if author_text:
        article['author'] = author_text
    
    # 提取正文
    content_elem = soup.select_one('article') or soup.select_one('[class*="article-content"]')
    if content_elem:
        for tag in content_elem.select('script, style'):
            tag.decompose()
        article['content'] = content_elem.get_text(strip=True)
    
    # 提取图片
    for img in soup.select('article img, img[src*="/Portals/"]'):
        img_data = {
            'src': img.get('src', ''),
            'alt': img.get('alt', ''),
            'title': img.get('title', '')
        }
        if img_data['src']:
            article['images'].append(img_data)
    
    # 提取视频
    for iframe in soup.select('iframe[src*="youtube"], iframe[src*="youku"], [class*="video"]'):
        if iframe.get('src'):
            article['videos'].append({
                'src': iframe.get('src', ''),
                'type': 'iframe'
            })
    
    return article


def fetch_globaltimes_list(page=1):
    """爬取环球时报新闻列表 - 国际频道"""
    url = f'https://www.globaltimes.cn/world/index.html'
    resp = requests.get(url)
    resp.encoding = 'utf-8'
    soup = BeautifulSoup(resp.content, 'html.parser')
    
    articles = []
    
    # 查找所有新闻链接
    for link in soup.select('a[href*="/page/"]'):
        href = link.get('href')
        if href and '/page/' in href:
            # 补全URL
            if not href.startswith('http'):
                href = 'https://www.globaltimes.cn' + href
            
            text = link.get_text(strip=True)
            if text and len(text) > 10:  # 避免很短的文本
                articles.append({
                    'title': text,
                    'url': href
                })
    
    return articles
```

---

## 注意事项

### 1. JavaScript 渲染
- **Al Jazeera**: 使用 React，首页列表可能需要 Selenium 或 Playwright
- **环球时报**: 大部分内容静态渲染，BeautifulSoup 可用

### 2. 反爬虫措施
- 添加 User-Agent
- 设置合理的请求延迟 (1-3秒)
- 遵守 robots.txt

### 3. 时间格式
- **Al Jazeera**: ISO 8601 格式 (`2026-03-19T...Z`)
- **环球时报**: 人类可读格式 (`Mar 20, 2026 12:04 AM`)

### 4. 字符编码
- **Al Jazeera**: UTF-8 (英文)
- **环球时报**: UTF-8 (中文)

### 5. 图片处理
- 两个网站都可能使用 CDN 加载图片
- 需要检查 CORS 策略
- 考虑下载和保存图片

### 6. 更新频率建议
- **Al Jazeera**: 每小时检查一次 (新闻频繁)
- **环球时报**: 每3-6小时检查一次 (更新稍慢)
