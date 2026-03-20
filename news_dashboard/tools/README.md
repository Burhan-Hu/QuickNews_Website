# News Dashboard 工具集

本文件夹包含了调试和测试的工具脚本。

## 工具列表

### 1. `debug.py` - 爬虫调试工具
检查各个爬虫网站的HTML结构和爬虫工作情况。

**使用方法：**
```bash
python -m news_dashboard.tools.debug
# 或在news_dashboard目录中
python -m tools.debug
```

**功能：**
- 调试Al Jazeera页面结构
- 调试环球时报页面结构
- 调试央视网页面结构
- 显示标题、时间、正文、图片、视频等元素信息

### 2. `check_structure.py` - 网站结构检查
快速检查网站的HTML容器和链接结构。

**使用方法：**
```bash
python -m news_dashboard.tools.check_structure
# 或在news_dashboard目录中
python -m tools.check_structure
```

**功能：**
- 检查SCMP、CNN、Al Jazeera、环球时报等网站
- 显示容器选择器的匹配情况
- 统计新闻链接数量
- 显示样本链接

### 3. `test_sites.py` - 爬虫快速测试
测试各个爬虫的工作情况，显示获取的文章数和详细信息。

**使用方法：**
```bash
# 测试所有网站
python -m news_dashboard.tools.test_sites

# 显示详细信息
python -m news_dashboard.tools.test_sites --verbose

# 只测试单个网站
python -m news_dashboard.tools.test_sites --single xinhua

# 显示错误详情
python -m news_dashboard.tools.test_sites --debug
```

**支持的网站：**
- xinhua (新华网)
- scmp (SCMP)
- cnn (CNN)
- nytimes (纽约时报)
- cctv (央视网)
- aljazeera (Al Jazeera)
- globaltimes (环球时报)

**功能：**
- 显示每个网站爬取的文章数
- 显示爬取耗时
- 显示第一条文章的详细信息（标题、来源、时间、正文长度、媒体数量）
- 支持详细输出和调试模式

## 工作流

### 开发新爬虫时：
1. 使用 `check_structure.py` 快速检查目标网站的HTML结构
2. 使用 `debug.py` 调试具体的CSS选择器和数据提取
3. 使用 `test_sites.py` 验证爬虫的实际效果

### 定期維護：
1. 定期运行 `test_sites.py` 检查所有爬虫的工作状态
2. 如果某个网站爬虫失效，使用 `debug.py` 诊断问题
3. 使用 `check_structure.py` 了解网站结构变化

## 环境要求

- Python 3.7+
- requests
- beautifulsoup4
- lxml

## 示例输出

```
$ python -m tools.test_sites

============================================================
  🚀 爬虫快速测试
============================================================

时间: 2026-03-20 17:00:00
Python: 3.13

▶ 新华网
--------------------------------------------------
状态: ✓ SUCCESS
耗时: 2.34 秒
获取文章数: 18 条

第一条文章:
  标题: 习近平致电巴西总统卢拉...
  来源: 新华网-时政
  时间: 2026-03-20 10:30:00
  正文: 1250 字
  媒体: 图2 视0

...
```

## 常见问题

### Q: 某个爬虫突然返回0条？
A: 
1. 先用 `test_sites.py --single <site>` 确认问题
2. 用 `debug.py` 检查网站的HTML结构是否改变
3. 用 `check_structure.py` 查看选择器是否还有效
4. 根据情况更新html_fetcher.py中的选择器

### Q: 爬虫运行很慢？
A: 
1. 检查网络连接
2. 增加超时时间（在html_fetcher.py中修改timeout参数）
3. 减少爬取的链接数量（修改limit参数）

### Q: 如何添加新网站？
A:
1. 在html_fetcher.py中添加新的fetch_xxx()方法
2. 用check_structure.py验证网站结构
3. 用debug.py调试数据提取逻辑
4. 用test_sites.py验证最终效果
5. 在fetch_all_domestic()中注册新方法
