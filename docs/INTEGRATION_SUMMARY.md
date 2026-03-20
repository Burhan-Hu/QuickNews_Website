# Workspace 整合说明

本文档记录了workspace的整合过程和最终结构。

## 整合内容

### 脚本文件整合

以下外部脚本已整合到 `news_dashboard/tools/` 目录中：

| 原文件 | 新位置 | 说明 |
|--------|--------|------|
| `debug_fetchers.py` | `news_dashboard/tools/debug.py` | 爬虫HTML结构调试工具 |
| `check_structures.py` | `news_dashboard/tools/check_structure.py` | 网站HTML结构检查工具 |
| `quick_test.py` | `news_dashboard/tools/test_sites.py` | 爬虫快速测试工具 |
| `test_xinhua_struct.py` | 已删除（功能已集成） | 功能已集成到其他工具中 |

### 代码整合

| 文件 | 说明 |
|------|------|
| `NEW_SITE_FETCHERS.py` | 其中的爬虫方法已整合到 `news_dashboard/core/html_fetcher.py` |
| - | 包括：fetch_nytimes()、fetch_cctv()、fetch_aljazeera()、fetch_globaltimes() |

## 最终目录结构

```
d:\qknews\
├── news_dashboard/              # 主应用（推荐的工作目录）
│   ├── main.py                  # 主入口
│   ├── requirements.txt          # 依赖列表
│   ├── test.py                  # 单元测试
│   ├── config/                  # 配置模块
│   │   ├── db_config.py
│   │   ├── sources.py
│   │   └── __init__.py
│   ├── core/                    # 核心爬虫模块
│   │   ├── fetcher.py          # RSS/NewsAPI爬虫
│   │   ├── html_fetcher.py     # HTML直接爬虫（7个网站）
│   │   ├── processor.py        # 内容处理器
│   │   ├── storage.py          # 数据存储
│   │   └── __init__.py
│   ├── scheduler/               # 定时任务模块
│   │   ├── jobs.py             # 调度任务
│   │   └── __init__.py
│   ├── tools/                   # 调试和测试工具（新增）
│   │   ├── __init__.py
│   │   ├── README.md           # 工具使用说明
│   │   ├── debug.py            # 爬虫调试
│   │   ├── check_structure.py  # 结构检查
│   │   └── test_sites.py       # 爬虫测试
│   └── certs/                   # 证书文件
│
├── db/                          # 数据库脚本
│   ├── Schema.sql
│   └── test.sql
├── docs/                        # 文档
│
└── 根目录文档（可归档到docs/）
    ├── README.md               # 保留（主文档）
    ├── .gitignore              # 保留
    ├── CRAWLERS_SUMMARY.md     # 可归档
    ├── README_CRAWLERS.md      # 可归档
    ├── NEWS_SITES_STRUCTURE_ANALYSIS.md  # 可归档
    └── 其他.md文档
```

## 工具使用指南

整合后的工具可以通过以下方式使用：

### 在项目根目录运行
```bash
cd d:\qknews\news_dashboard
python -m tools.test_sites
python -m tools.debug
python -m tools.check_structure
```

### 或直接运行
```bash
cd d:\qknews\news_dashboard\tools
python test_sites.py
python debug.py
python check_structure.py
```

## 文件清理建议

以下原始文件已整合，可以备份后删除：

1. `d:\qknews\debug_fetchers.py` → 已整合到 `tools/debug.py`
2. `d:\qknews\check_structures.py` → 已整合到 `tools/check_structure.py`
3. `d:\qknews\quick_test.py` → 已整合到 `tools/test_sites.py`
4. `d:\qknews\test_xinhua_struct.py` → 功能已集成

### 可归档的文档（移到docs/）
- CRAWLERS_SUMMARY.md
- README_CRAWLERS.md
- README_NEW_SITES.md
- WEBSITE_ANALYSIS.md
- NEWS_SITES_STRUCTURE_ANALYSIS.md
- INTEGRATION_GUIDE.md
- QUICK_REFERENCE.md
- FILE_CHECKLIST.md

## 整合的好处

1. **统一管理**：所有工具集中在news_dashboard/tools中，易于查找和维护
2. **清晰结构**：区分了应用代码和工具脚本，模块化更强
3. **易于运行**：开发者可以一致地运行tools下的脚本
4. **版本控制**：workspace更整洁，核心代码和工具分离

## 后续步骤

1. ✅ 完成：脚本整合到tools/
2. ✅ 完成：创建tools/README.md
3. 建议：删除或移动原始脚本文件到归档文件夹
4. 建议：整理根目录的markdown文档到docs/文件夹
5. 可选：在requirements.txt中添加开发依赖说明

## 验证整合

运行以下命令验证整合是否成功：

```bash
# 验证tools模块可导入
cd d:\qknews\news_dashboard && python -c "import tools; print('OK')"

# 运行测试
python -m tools.test_sites --single xinhua

# 运行调试
python -m tools.debug
```
