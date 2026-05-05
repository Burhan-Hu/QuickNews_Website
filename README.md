# QuickNews — 多源新闻聚合与可视化信息检索系统

> NKU 信息检索系统课程大作业 | 数据库系统课程大作业

## 项目简介

QuickNews 是一个面向全球新闻的多源聚合与可视化信息检索系统。系统遵循信息检索的标准流水线——**采集 (Acquisition) → 处理 (Processing) → 存储 (Storage) → 检索 (Retrieval) → 展示 (Presentation)**——实现了从多源异构数据采集、中英文分词与实体识别、关系型数据库存储与倒排索引构建，到基于 SRU 协议的字段/布尔检索、3D 地球热力图可视化的完整闭环。

系统已部署至阿里云 ECS，7×24 小时自动运行。

## 在线演示

**访问地址**：http://47.239.168.183

| 页面 | 功能 |
|------|------|
| `/` | 系统首页 — 3D 地球入口 |
| `/search` | 新闻搜索 — SRU 检索、分类浏览 |
| `/visual` | 新闻可视化 — 3D 地球热力图、热点话题、国家新闻 |
| `/news/:id` | 新闻详情 — 正文、图片、视频、原文链接 |

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18 + Vite + Three.js (3D 地球) + Tailwind CSS |
| 后端 | Flask + Flask-CORS + Gunicorn |
| 数据库 | MySQL 8.0 (Aiven Cloud) + SQLAlchemy + PyMySQL |
| 爬虫 | Requests + FeedParser + curl_cffi (TLS 指纹模拟) + APScheduler |
| 分词/NLP | Jieba (中文) + 自定义停用词表 |
| 部署 | Nginx 反向代理 + Systemd 进程守护 + 阿里云 ECS |

---

## 信息检索核心功能

### 1. 信息采集 (Information Acquisition)

系统支持三类异构数据采集，覆盖中英文主流新闻源：

- **RSS 订阅**：36氪、The Atlantic、RT-中文、FoxNews、南华早报-SCMP、ChinaDaily、The New Yorker、AP-美联社、经济日报、iDaily、RFI-中文
- **HTML 网页爬取**：界面新闻、新华网、环球时报、俄罗斯卫星通讯社(Sputnik)、纽约时报-中文、半岛电视台(Al Jazeera)、BBC
- **NewsAPI**：国际新闻 API（100 次/日配额，类别+国家轮询）

爬虫采用 **APScheduler** 定时调度，每 20 分钟执行一轮抓取，对超过 20 个来源进行并发/串行采集。HTML 爬取使用 **curl_cffi** 模拟 Chrome TLS 指纹，绕过部分站点的反爬策略。RSS 抓取若遇到仅含图片的摘要，自动降级至详情页二次抓取全文。

### 2. 信息处理 (Information Processing)

每篇新闻入库前经过完整的处理流水线：

- **HTML 清洗**：基于 `HTMLParser` 去除标签，提取纯文本正文
- **语言检测**：中文字符启发式判断（含 `\u4e00-\u9fff` 即为 `zh`，否则为 `en`）
- **中文分词**：Jieba `lcut` → 停用词过滤 → 保留长度≥2 的有效词
- **英文分词**：空格分词 → 停用词过滤 → 保留长度≥2 的有效词
- **国家识别**：基于 `country_keywords` 关键词库的标题优先匹配策略。标题中出现国家关键词则标记为主要关联国；标题无匹配时回退至正文统计
- **自动分类**：MySQL 存储过程 `sp_insert_news` 根据来源 ID 与内容关键词自动分配至科技/政治/经济/军事/文化/体育类别

### 3. 信息存储 (Information Storage)

数据库采用 **MySQL 关系模型**，核心实体包括：

| 表 | 作用 |
|----|------|
| `news` | 新闻主表（标题、摘要、正文、URL、来源 ID、语言） |
| `sources` | 新闻来源配置（名称、URL、类型、语言、可信度） |
| `categories` | 分类表（科技、政治、经济、军事、文化、体育） |
| `countries` | 国家表（ISO 代码、名称、地区） |
| `country_keywords` | 国家识别关键词库（国家代码 ↔ 关键词映射） |
| `xml_index` | **倒排索引表**（term → 文档列表 XML） |
| `hot_topics` | 热点话题表（话题名、新闻数量、最后更新时间） |
| `news_topics` | 新闻-话题关联表（支持代表新闻标记） |
| `news_countries` | 新闻-国家关联表（支持主要国家标记） |
| `media` | 媒体资源表（图片、视频 URL） |

**倒排索引机制**：
- 新闻入库时，存储过程 `sp_build_xml_index` 自动对标题和正文分词
- 每个 term 在 `xml_index` 表中维护一个 XML 文档列表，记录包含该词的新闻 ID、词频、字段类型（title/content）
- 检索时直接查 `xml_index` 表，无需实时分词，保证查询效率

**数据清理**：
- MySQL Event Scheduler 每 30 分钟执行 `sp_cleanup_48h`，自动清理 48 小时前的过期新闻，控制数据规模

### 4. 信息检索 (Information Retrieval)

系统实现了基于 **SRU (Search/Retrieve via URL)** 协议的搜索接口，支持多种检索模式：

| 检索类型 | 示例 | 说明 |
|----------|------|------|
| 关键词检索 | `Trump` | 在标题和正文中检索 |
| 字段检索 | `title:中国` | 仅在标题中检索 |
| 布尔检索 | `war OR conflict` | 包含任一关键词 |
| 通配检索 | `*` | 返回最新新闻 |

**检索流程**：
1. 解析查询词，提取字段限定符（`title:`、`country:`）
2. 对非限定词进行分词
3. 查 `xml_index` 倒排索引，获取各 term 的文档列表
4. 执行布尔运算（AND 取交集、OR 取并集）
5. 按综合相关性排序（标题命中权重 > 正文命中权重）
6. 返回 XML 格式标准 SRU 响应

**API 端点**：
- `GET /sru?query=关键词&maximumRecords=20` — SRU 搜索
- `GET /api/search?query=关键词` — JSON 格式搜索
- `GET /api/news/category/politics` — 按分类检索
- `GET /api/news/198` — 单条新闻详情

### 5. 信息展示 (Information Presentation)

- **3D 地球热力图**：基于 Three.js 的交互式地球模型，国家新闻数量映射为柱状高度和颜色热度。点击国家加载该国相关新闻列表
- **热点话题云**：基于 LCS (Longest Common Subsequence) 相似度对新闻标题聚类，提取代表性话题。每小时自动更新
- **地区热度排行**：右侧面板展示新闻量 Top 10 国家列表
- **新闻详情页**：支持图片画廊、视频播放器（YouTube / Bilibili 嵌入）、原文链接跳转
- **分类浏览**：搜索页支持科技、政治、经济、军事、文化、体育六类快速筛选

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        用户浏览器                            │
│              React + Three.js (3D 地球可视化)                │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP
┌──────────────────────────▼──────────────────────────────────┐
│                         Nginx                               │
│    静态文件 (app/dist)  │  API 反向代理 (/api/* → Flask)   │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┴──────────────────┐
        ▼                                      ▼
┌───────────────┐                    ┌───────────────────────┐
│   Flask API   │                    │   Systemd Timer       │
│  /sru 搜索    │                    │  qknews-crawler       │
│  /api/*       │                    │  (每20分钟)           │
│  /health      │                    │  qknews-topics        │
└───────┬───────┘                    │  (每小时)             │
        │                            └───────────┬───────────┘
        │                                        │
        ▼                                        ▼
┌───────────────┐                      ┌─────────────────┐
│  Aiven MySQL  │◄─────────────────────│  多源爬虫引擎   │
│  关系型数据库  │      存储/查询        │  RSS/HTML/API   │
│  + 倒排索引   │                      │  + 分词处理     │
└───────────────┘                      └─────────────────┘
```

---

## 本地运行指南

### 环境要求
- Python 3.10+
- Node.js 18+
- MySQL 8.0+（或远程 Aiven 实例）

### 1. 克隆项目
```bash
git clone https://github.com/Burhan-Hu/QuickNews_Website.git
cd QuickNews_Website
```

### 2. 配置数据库
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env，填入数据库连接信息
DB_HOST=your-mysql-host
DB_PORT=3306
DB_USER=your-username
DB_PASSWORD=your-password
DB_NAME=quicknews_maindb
CORS_ORIGINS=http://localhost:5173
```

### 3. 初始化数据库
```bash
# 使用 MySQL 客户端导入 schema
mysql -u your_username -p your_database < db/schema.sql
```

### 4. 安装后端依赖
```bash
cd news_dashboard
pip install -r requirements.txt
```

### 5. 安装前端依赖并构建
```bash
cd ../app
npm install
npm run build
```

### 6. 启动后端（开发模式）
```bash
cd ../news_dashboard
python main.py
# 或生产模式：gunicorn -w 2 -b 127.0.0.1:5000 wsgi:app
```

### 7. 启动前端（开发模式）
```bash
cd ../app
npm run dev
# 访问 http://localhost:5173
```

---

## 项目结构

```
QuickNews_Website/
├── news_dashboard/           # Flask 后端
│   ├── ir/
│   │   └── xml_api.py        # SRU 搜索 API + 倒排索引查询
│   ├── core/
│   │   ├── processor.py      # 分词 + 国家识别 + 语言检测
│   │   ├── fetcher.py        # RSS/HTML/API 多源爬虫
│   │   ├── html_fetcher.py   # HTML 详情页抓取
│   │   ├── storage.py        # 数据库写入 + 存储过程调用
│   │   └── stopwords.py      # 中英文停用词表
│   ├── scheduler/
│   │   └── jobs.py           # APScheduler 定时任务
│   ├── config/
│   │   ├── db_config.py      # 数据库引擎配置
│   │   └── sources.py        # 新闻源配置
│   ├── main.py               # 本地开发入口
│   ├── wsgi.py               # WSGI 生产入口
│   ├── cron_fetch.py         # 爬虫 Cron 脚本
│   └── cron_topics.py        # 话题更新 Cron 脚本
├── app/                      # React 前端
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Search.jsx    # 搜索页
│   │   │   ├── Visual.jsx    # 3D 可视化页
│   │   │   └── NewsDetail.jsx  # 新闻详情页
│   │   ├── components/
│   │   │   └── Earth3D.jsx   # Three.js 地球组件
│   │   └── utils/
│   │       ├── api.js        # 后端 API 调用
│   │       └── countryCoords.js  # 国家坐标数据
│   └── dist/                 # 构建产物
├── db/
│   └── schema.sql            # 完整数据库 Schema（含触发器、存储过程）
├── docs/                     # 项目文档
├── deploy_aliyun.sh          # 阿里云 ECS 一键部署脚本
└── README_HW3.md             # 本文件
```

---

## 关键设计决策

1. **为什么用 MySQL + XML 倒排索引，而不是 Elasticsearch？**
   - 课程要求展示对数据库原理的理解，MySQL 的存储过程、触发器、Event Scheduler 更能体现数据库设计能力
   - XML 格式的 `xml_index` 表在万级文档规模下查询性能足够，且实现简洁

2. **为什么采用标题优先的国家识别策略？**
   - 新闻标题通常明确提及国家，正文可能包含大量无关国家的地名（如"华盛顿会议"不必然关联美国）
   - 标题优先比全文统计准确率更高

3. **为什么使用 SRU 协议而不是自定义 JSON 搜索？**
   - SRU 是图书馆与信息检索领域的标准协议，支持字段检索、布尔运算、分页排序
   - 更符合信息检索课程的学术规范

---

## 作者信息

- **学号**：____2410886____
- **姓名**：___胡博涵_______
- **学校**：南开大学
- **提交日期**：2026 年 5 月
