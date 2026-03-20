# 新闻网站HTML结构分析报告

基于对4个新闻网站的探索，以下是爬取策略和HTML选择器总结。

---

## 1. 纽约时报中文版 (https://cn.nytimes.com/)

### 列表页URL结构
```
首页：https://cn.nytimes.com/
频道页面：https://cn.nytimes.com/china/  （中国频道）
         https://cn.nytimes.com/business/  （商业频道）
         https://cn.nytimes.com/world/     （国际频道）
```

### 具体新闻URL示例
```
https://cn.nytimes.com/usa/20260320/trump-netanyahu-iran-gas-field-attack/zh-hant/
https://cn.nytimes.com/world/20260319/israel-us-iran-strategy-war/zh-hant/
https://cn.nytimes.com/business/20260320/dubai-luxury-shopping-iran-war/zh-hant/
https://cn.nytimes.com/china/20260317/china-zhou-dynasty-king-climate-change/zh-hant/
```

### HTML结构分析

#### 列表页选择器
```python
# 新闻列表容器（使用开发者工具检查）
list_container = soup.select('div[class*="article-list"]')  # 待确认
# 或通过标题选择
article_items = soup.select('h2, h3')  # 文章标题

# 单条新闻项（待完整分析）
title_selector = 'h2, h3'  # 标题
link_selector = 'a'  # 链接
time_selector = 'time, span[class*="time"]'  # 时间
```

#### 详情页选择器
```python
# 正文容器
article_content = soup.select('article')[0]
# 或
article_body = soup.select('div[class*="body"], div[class*="content"]')

# 文章标题
title = soup.select('h1')[0]

# 发布时间（格式：HH:MM）
pub_time = soup.find('time')  # <time> 标签

# 作者
author = soup.select('span[class*="author"], div.byline')

# 摘要/副标题
summary = soup.select('h2[class*="subheading"]')
```

#### 图片和视频
```python
# 图片元素（在正文中）
images = article_body.find_all('img')  # <img src="..." alt="...">

# 视频（如果有）
videos = article_body.find_all('video')  # <video> 标签
# 或 iframe 嵌入（待确认）
video_iframes = article_body.find_all('iframe')
```

### 爬取方法框架
```python
def fetch_nytimes(article_url):
    """
    爬取纽约时报文章
    Args:
        article_url: 文章URL
    Returns:
        dict: 包含标题、正文、时间、图片等信息
    """
    response = requests.get(article_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    article_data = {
        'title': soup.find('h1').text.strip() if soup.find('h1') else '',
        'url': article_url,
        'pub_time': None,  # 从time标签提取
        'author': '',
        'content': '',  # 从 <article> 提取所有文本
        'images': [],  # 提取所有 <img> 的 src 属性
        'videos': [],  # 提取所有 <video> 和 <iframe>
        'summary': ''
    }
    
    # 详细实现待补充...
    return article_data
```

---

## 2. 央视网 (https://www.cctv.com/)

### 列表页URL结构
```
首页：https://www.cctv.com/
新闻频道：https://news.cctv.com/
国际新闻：https://news.cctv.com/world/
体育频道：https://sports.cctv.com/
视频频道：https://v.cctv.com/
```

### 具体新闻URL示例
```
文字新闻：https://news.cctv.com/2026/03/20/ARTIO9yk1BtpGKUTsT5Q1LxJ260320.shtml
视频新闻：https://v.cctv.com/2026/03/20/VIDEyiW5gC5sxjZqP5G1Qm1l260320.shtml
         https://tv.cctv.com/2026/03/19/VIDE20vv4xyXMRufd9krA9kG260319.shtml
体育新闻：https://sports.cctv.com/2026/03/20/ARTIznigBeqvtU3wjfAplNmD260320.shtml
```

### HTML结构分析

#### 列表页选择器
```python
# 新闻列表结构
# 央视使用多种列表容器格式，常见的有：
list_items = soup.select('li[class*="clearfix"]')  # 列表项
# 或
list_items = soup.select('div[class*="tlist"]')

# 单条新闻项
title = item.select_one('h2, h3, a')  # 标题链接
link = item.select_one('a')['href']  # 提取 href 属性
time_elem = item.select_one('span[class*="time"]')  # 时间戳
```

#### 详情页选择器（文字新闻）
```python
# 正文容器
article_body = soup.select_one('div[class*="content"]')
# 或更具体
article_body = soup.select_one('div.content, div#content, div.article-content')

# 标题
title = soup.select_one('h1, div[class*="title"] h1')

# 发布时间（格式：2026/03/20 HH:MM来源：CCTV）
time_info = soup.select_one('span[class*="time"]')  # 可能包含完整的时间和来源

# 摘要（如果有）
summary = soup.select_one('div[class*="summary"], p[class*="summary"]')
```

#### 详情页选择器（视频新闻）
```python
# 视频容器
video_container = soup.select_one('div[class*="video"]')

# 视频标题
video_title = soup.select_one('h1')

# 视频来源的分类标签
category = soup.select_one('a[class*="column"]')

# 视频描述
video_desc = soup.select_one('div[class*="intro"], p[class*="desc"]')
```

#### 图片和视频元素
```python
# 图片（新闻中的插图）
images = article_body.find_all('img')  # <img src="..." alt="...">
# 图片链接通常使用 p1.img.cctvpic.com、p2.img.cctvpic.com 等

# 视频元素（视频详情页）
video_player = soup.select_one('div[id*="video"], video')
# 央视网视频可能使用：
# 1. <video> 标签 + <source>
video_sources = video_player.find_all('source')  # src 属性包含视频 URL
# 2. 或 JavaScript 初始化参数（可能需要 selenium）

# 视频截图/封面
video_image = soup.select_one('img[class*="thumbnail"], img[alt*="视频"]')
```

### 爬取方法框架
```python
def fetch_cctv(article_url):
    """
    爬取央视网文章（支持视频和文字新闻）
    Args:
        article_url: 文章URL (news.cctv.com 或 v.cctv.com 或 tv.cctv.com)
    Returns:
        dict: 包含标题、正文、时间、图片等信息
    """
    response = requests.get(article_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    is_video = 'v.cctv.com' in article_url or 'tv.cctv.com' in article_url
    
    article_data = {
        'title': '',
        'url': article_url,
        'pub_time': '',  # 从时间元素提取
        'category': '',  # 从分类标签提取
        'content': '',  # 正文文本
        'images': [],  # 所有图片 URL
        'videos': [],  # 视频信息（URL、截图等）
        'is_video': is_video
    }
    
    # 详细实现待补充...
    return article_data
```

---

## 3. 观察者网 (https://www.guancha.cn/)

### 列表页URL结构
```
首页：https://www.guancha.cn/
国际新闻：https://www.guancha.cn/america/
政治新闻：https://www.guancha.cn/politics/
评论频道：https://www.guancha.cn/opinion/
```

### 具体新闻URL示例（需要实际访问获取）
```
预计格式：https://www.guancha.cn/america/2026_03_20_xxx.html
         https://www.guancha.cn/politics/2026_03_20_xxx.html
```

### HTML结构分析（待完整分析）

#### 列表页选择器（预估）
```python
# 列表容器
list_items = soup.select('div[class*="articles"], ul[class*="list"]')

# 单条新闻
title = item.select_one('h2, h3, a')
link = item.select_one('a')['href']
time_elem = item.select_one('span[class*="time"]')
summary = item.select_one('p[class*="summary"]')
```

#### 详情页选择器
```python
# 正文内容
article_body = soup.select_one('div[class*="article"], div.content')

# 标题、时间、作者等元数据
title = soup.find('h1')
pub_time = soup.select_one('span[class*="date"], time')
author = soup.select_one('span[class*="author"]')

# 图片和视频
images = article_body.find_all('img')
videos = article_body.find_all('iframe')  # 可能嵌入视频
```

### 爬取方法框架
```python
def fetch_guancha(article_url):
    """
    爬取观察者网文章
    """
    # 待实现
    pass
```

---

## 4. 华盛顿邮报 (https://www.washingtonpost.com/)

### 访问限制
- 网站可能有反爬虫机制（需要 User-Agent 和请求头）
- 部分内容可能需要登录/订阅
- 推荐使用 selenium 或添加适当的请求头

### 列表页URL结构
```
首页：https://www.washingtonpost.com/
美国新闻：https://www.washingtonpost.com/us-news/
国际新闻：https://www.washingtonpost.com/world/
政治：https://www.washingtonpost.com/politics/
```

### 具体新闻URL示例（需要实际访问）
```
预计格式：https://www.washingtonpost.com/[section]/202X/XX/XX/xxxxx/
```

### 爬取建议
```python
import requests
from bs4 import BeautifulSoup

# 必要的请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def fetch_washingtonpost(article_url):
    """
    爬取华盛顿邮报文章
    需要处理：
    1. 反爬虫机制
    2. 动态加载内容（可能需要 selenium）
    3. 付费墙（部分内容限制）
    """
    response = requests.get(article_url, headers=HEADERS)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # 待实现 HTML 结构分析
    pass
```

---

## 通用爬取建议

### 1. 请求配置
```python
import requests
from bs4 import BeautifulSoup
import time

# 通用请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

def fetch_article(url, timeout=10):
    """
    通用文章爬取函数
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
        response.encoding = 'utf-8'  # 确保正确的编码
        return BeautifulSoup(response.content, 'html.parser')
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None
```

### 2. 常用选择器模式
```python
# 查找标题
title = soup.find('h1') or soup.select_one('h1, div[class*="title"] h1')

# 查找时间
time_elem = soup.find('time') or soup.select_one('span[class*="time"], span[class*="date"]')

# 查找作者
author = soup.select_one('span[class*="author"], a[rel="author"]')

# 查找正文
content = soup.find('article') or soup.select_one('div[class*="content"], div[class*="body"]')

# 查找图片
images = content.find_all('img') if content else []

# 查找视频
videos = content.find_all('video') if content else []
iframes = content.find_all('iframe') if content else []
```

### 3. 数据提取示例
```python
def extract_article_data(soup, url):
    """
    从 BeautifulSoup 对象中提取文章数据
    """
    article = {
        'url': url,
        'title': '',
        'pub_time': '',
        'author': '',
        'content': '',
        'images': [],
        'videos': [],
        'source': get_source_from_url(url)  # 从 URL 判断来源
    }
    
    # 提取标题
    title_elem = soup.find('h1')
    if title_elem:
        article['title'] = title_elem.get_text(strip=True)
    
    # 提取时间
    time_elem = soup.find('time')
    if time_elem:
        article['pub_time'] = time_elem.get('datetime') or time_elem.get_text(strip=True)
    
    # 提取内容
    content_elem = soup.find('article') or soup.select_one('div[class*="content"]')
    if content_elem:
        article['content'] = content_elem.get_text(strip=True)
        
        # 提取图片
        for img in content_elem.find_all('img'):
            img_url = img.get('src') or img.get('data-src')
            if img_url and img_url not in article['images']:
                article['images'].append(img_url)
        
        # 提取视频
        for video in content_elem.find_all('video'):
            source = video.find('source')
            if source:
                article['videos'].append({
                    'url': source.get('src'),
                    'type': source.get('type')
                })
        
        for iframe in content_elem.find_all('iframe'):
            article['videos'].append({
                'url': iframe.get('src'),
                'type': 'iframe'
            })
    
    return article

def get_source_from_url(url):
    """从 URL 判断新闻来源"""
    if 'nytimes.com' in url:
        return 'nytimes'
    elif 'cctv.com' in url:
        return 'cctv'
    elif 'guancha.cn' in url:
        return 'guancha'
    elif 'washingtonpost.com' in url:
        return 'washingtonpost'
    return 'unknown'
```

### 4. 错误处理和重试
```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session_with_retry():
    """创建带重试机制的 requests 会话"""
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=(500, 502, 504)
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

# 使用
session = create_session_with_retry()
response = session.get(url, headers=HEADERS)
```

---

## 实现优先级

**高优先级**（容易实现）:
- [ ] `fetch_nytimes()`: 结构清晰，选择器获取相对容易
- [ ] `fetch_cctv()`: 结构明确，支持文字和视频新闻

**中优先级**（需要完整分析）:
- [ ] `fetch_guancha()`: 需要实际访问获取 HTML 结构
- [ ] `fetch_washingtonpost()`: 需要处理反爬虫机制

---

## 下一步建议

1. **逐个测试**：为每个网站编写简单测试脚本，确认选择器有效
2. **动态内容**：如果网站使用 JavaScript 加载内容，改用 Selenium
3. **数据验证**：添加数据验证和清理逻辑
4. **存储方案**：集成到现有的 storage.py 模块

