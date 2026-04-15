# TrendRadar 项目地图

> 版本：6.6.0 | 最后更新：2026-04-15

---

## 项目概览

**TrendRadar** 是一个热点新闻聚合与分析工具，主要功能：

- 从 NewsNow API 和 RSS 订阅源抓取多平台热榜数据
- 将数据存入本地 SQLite 或 S3 兼容远程存储
- 生成 HTML 报告，并通过飞书/钉钉/Telegram/邮件等渠道推送
- 可选接入 LiteLLM（AI 分析、翻译、智能筛选）
- 通过 FastMCP 2.0 将数据和操作暴露为 MCP 工具，供 AI 助手调用

---

## 目录结构

```
/workspace
├── trendradar/          # 主包：爬虫 + 分析 + 通知 + 存储 + AI
├── mcp_server/          # MCP Server 包：FastMCP 工具服务器
├── docker/              # Docker 相关文件及容器管理脚本
├── config/              # 配置文件（config.yaml、关键词、AI 提示词等）
├── docs/                # 静态文档站点
├── .github/workflows/   # CI/CD 工作流
└── output/              # 运行时输出目录（自动创建，不入库）
```

---

## 第一部分：trendradar 主包

### 入口 & 顶层

| 文件 | 用途 |
|------|------|
| `trendradar/__main__.py` | **主程序入口**。包含 `NewsAnalyzer`（完整爬取→分析→推送流水线）、`main()`（CLI 解析）及诊断命令 `--doctor` / `--test-notification` / `--show-schedule` |
| `trendradar/__init__.py` | 包元数据；导出 `AppContext`、`__version__` |
| `trendradar/context.py` | `AppContext`：全局应用上下文，串联配置加载、存储、报告生成、通知分发、AI 过滤/翻译 |

**运行命令：**

```bash
# 正常运行（抓取 + 分析 + 推送）
python -m trendradar

# 查看当前调度状态
python -m trendradar --show-schedule

# 一键环境体检（检查 Python 版本、配置文件、AI 配置、通知渠道等）
python -m trendradar --doctor

# 测试通知渠道连通性
python -m trendradar --test-notification
```

**前置条件：**
- Python ≥ 3.12，已安装依赖（`pip install -e .` 或 `uv sync`）
- `config/config.yaml`（必须）
- `config/frequency_words.txt`（必须）
- `config/timeline.yaml`（可选，调度配置）

---

### core/ 核心逻辑

| 文件 | 用途 |
|------|------|
| `trendradar/core/config.py` | 多账号字符串解析（`;` 分隔）、配对校验（如 Telegram bot_token + chat_id） |
| `trendradar/core/loader.py` | 加载 `config.yaml`，处理环境变量覆盖（布尔、整数、通知块） |
| `trendradar/core/frequency.py` | 解析 `frequency_words.txt`：分组、必含/排除词、正则、全局过滤器、显示名 |
| `trendradar/core/scheduler.py` | 时间表调度器：解析 `timeline.yaml`，计算当前时间段的采集/分析/推送行为开关 |
| `trendradar/core/data.py` | 从存储读取今日标题；检测新增标题（用于增量模式） |
| `trendradar/core/analyzer.py` | 词频统计、排名显示、平台统计转换、RSS 关键词匹配 |
| `trendradar/core/__init__.py` | 重导出核心 API |

---

### crawler/ 爬虫

| 文件 | 用途 |
|------|------|
| `trendradar/crawler/fetcher.py` | `DataFetcher`：调用 NewsNow JSON API，支持重试和代理，返回各平台热榜数据 |
| `trendradar/crawler/rss/parser.py` | `RSSParser`：通过 feedparser 解析 RSS 2.0 / Atom / JSON Feed |
| `trendradar/crawler/rss/fetcher.py` | `RSSFetcher`：批量抓取 RSS 订阅源，支持间隔、年龄过滤、代理 |
| `trendradar/crawler/__init__.py` | 导出 `DataFetcher` |
| `trendradar/crawler/rss/__init__.py` | 导出 `RSSParser`、`RSSFetcher`、`RSSFeedConfig` |

---

### storage/ 存储

| 文件 | 用途 |
|------|------|
| `trendradar/storage/base.py` | 抽象基类 `StorageBackend`；数据模型 `NewsItem`、`NewsData`、`RSSItem`、`RSSData`；爬虫结果转换 |
| `trendradar/storage/sqlite_mixin.py` | SQLite CRUD/查询公共逻辑（被本地后端和远程后端共用） |
| `trendradar/storage/local.py` | 本地后端：写入 `output/` 下的 SQLite 文件，可选 TXT 快照 |
| `trendradar/storage/remote.py` | S3 兼容远程后端：下载 DB、合并、上传（boto3） |
| `trendradar/storage/manager.py` | 存储后端选择器（local / remote / auto）；单例 `get_storage_manager` |
| `trendradar/storage/__init__.py` | 导出存储 API |

**前置条件（远程存储）：**
- `config.yaml` 中配置 `storage.remote`，或设置环境变量：`S3_ENDPOINT_URL`、`S3_BUCKET_NAME`、`S3_ACCESS_KEY_ID`、`S3_SECRET_ACCESS_KEY`

---

### report/ 报告生成

| 文件 | 用途 |
|------|------|
| `trendradar/report/helpers.py` | 标题清洗、HTML 转义、排名显示字符串工具函数 |
| `trendradar/report/formatter.py` | `format_title_for_platform`：按渠道格式化标题（飞书/钉钉/HTML/Telegram 等） |
| `trendradar/report/generator.py` | `prepare_report_data`、`generate_html_report`：报告数据组装与 HTML 文件写入 |
| `trendradar/report/html.py` | 完整 HTML 报告模板（热榜 + RSS + AI 分析区块） |
| `trendradar/report/rss_html.py` | RSS 独立 HTML 报告模板（含 html2canvas CDN） |
| `trendradar/report/__init__.py` | 导出报告 API |

---

### notification/ 通知推送

| 文件 | 用途 |
|------|------|
| `trendradar/notification/formatters.py` | Markdown 清洗、Slack mrkdwn 转换 |
| `trendradar/notification/batch.py` | 批量消息头部、UTF-8 字节截断（防超限） |
| `trendradar/notification/renderer.py` | 将报告数据渲染为飞书/钉钉等渠道消息体 |
| `trendradar/notification/splitter.py` | 按平台字节上限分割长消息 |
| `trendradar/notification/senders.py` | 各渠道 HTTP/SMTP 发送实现（飞书、钉钉、企业微信、Telegram、邮件、ntfy、Bark、Slack、通用 Webhook） |
| `trendradar/notification/dispatcher.py` | `NotificationDispatcher.dispatch_all`：统一分发到所有已配置渠道，支持多账号 |
| `trendradar/notification/__init__.py` | 导出通知 API |

---

### ai/ 人工智能

| 文件 | 用途 |
|------|------|
| `trendradar/ai/client.py` | `AIClient`：LiteLLM `completion` 薄封装，配置校验 |
| `trendradar/ai/prompt_loader.py` | 从 `config/` 加载 `[system]` / `[user]` 提示词文件 |
| `trendradar/ai/analyzer.py` | `AIAnalyzer`：生成多区块 AI 分析报告（`AIAnalysisResult` 数据类） |
| `trendradar/ai/filter.py` | `AIFilter`：按兴趣列表批量分类标题（可回退到关键词匹配） |
| `trendradar/ai/translator.py` | `AITranslator`：批量翻译推送内容 |
| `trendradar/ai/formatter.py` | 将 `AIAnalysisResult` 渲染为飞书/钉钉/HTML/纯文本格式 |
| `trendradar/ai/__init__.py` | 导出 AI API |

**前置条件：**
- `config.yaml` 中 `ai.model` 和 `ai.api_key` 已填写，或设置环境变量 `AI_API_KEY`、`AI_MODEL`

---

### utils/ 工具

| 文件 | 用途 |
|------|------|
| `trendradar/utils/time.py` | 时区感知 `now()`、文件夹名格式、显示格式、天数计算 |
| `trendradar/utils/url.py` | `normalize_url`：去除追踪参数、平台专属 URL 规范化（用于去重） |
| `trendradar/utils/__init__.py` | 重导出时间和 URL 工具 |

---

## 第二部分：mcp_server 包

MCP Server 将 TrendRadar 的数据和操作通过 [Model Context Protocol](https://modelcontextprotocol.io/) 暴露给 AI 助手（如 Claude、ChatGPT 等）。

**运行命令：**

```bash
# stdio 模式（配合 MCP 客户端使用，如 Claude Desktop、Cherry Studio）
python -m mcp_server

# HTTP 模式（生产环境，默认端口 3333）
python -m mcp_server --transport http --port 3333

# 或使用安装后的命令
trendradar-mcp
trendradar-mcp --transport http --port 3333
```

**前置条件：**
- 同 trendradar 主包，需要 `config/config.yaml` 和数据文件
- 详细配置教程见 `README-Cherry-Studio.md`

### server.py — 主服务器文件

`mcp_server/server.py` 是 MCP Server 的唯一入口，注册了 30 个工具和 4 个资源：

| 工具组 | 工具列表 |
|--------|----------|
| 日期解析 | `resolve_date_range` |
| 基础数据查询 | `get_latest_news`、`get_news_by_date`、`get_trending_topics` |
| RSS 数据查询 | `get_latest_rss`、`search_rss`、`get_rss_feeds_status` |
| 智能检索 | `search_news`、`find_related_news` |
| 高级数据分析 | `analyze_topic_trend`、`analyze_data_insights`、`analyze_sentiment`、`aggregate_news`、`compare_periods`、`generate_summary_report` |
| 配置与系统管理 | `get_current_config`、`get_system_status`、`check_version`、`trigger_crawl` |
| 存储同步 | `sync_from_remote`、`get_storage_status`、`list_available_dates` |
| 文章内容读取 | `read_article`、`read_articles_batch` |
| 通知推送 | `get_channel_format_guide`、`get_notification_channels`、`send_notification` |
| 亚马逊商品图片 | `generate_amazon_image_workflow`、`get_amazon_image_specs`、`generate_amazon_creative_brief`、`generate_amazon_image_prompts` |

### tools/ MCP 工具实现

| 文件 | 用途 |
|------|------|
| `mcp_server/tools/data_query.py` | P0 数据查询工具：最新新闻、按日期查询、趋势话题、RSS 查询 |
| `mcp_server/tools/analytics.py` | 高级分析：趋势、生命周期、爆火检测、预测、平台对比、关键词共现、情感分析、聚合去重、时期对比、摘要报告 |
| `mcp_server/tools/search_tools.py` | 统一搜索：关键词/模糊/实体模式，支持同时搜索热榜和 RSS |
| `mcp_server/tools/config_mgmt.py` | 读取 `config.yaml` 各配置节（爬虫/推送/关键词/权重等） |
| `mcp_server/tools/system.py` | 系统状态、健康检查、版本对比、手动触发爬取 |
| `mcp_server/tools/storage_sync.py` | 从远程存储拉取数据、列出可用日期、存储状态查询 |
| `mcp_server/tools/article_reader.py` | 通过 Jina Reader API 将网页转为 Markdown（单篇/批量，内置限速 5 s/次） |
| `mcp_server/tools/notification.py` | 通过 MCP 向已配置渠道发送通知；获取渠道格式化指南 |
| `mcp_server/tools/amazon_listing.py` | 亚马逊商品图片工作流：规格查询、创意简报、AI 生图提示词（Midjourney/DALL-E/SD） |
| `mcp_server/tools/__init__.py` | 包标记 |

### services/ 数据服务层

| 文件 | 用途 |
|------|------|
| `mcp_server/services/data_service.py` | `DataService`：MCP 工具的统一数据入口，封装 `ParserService` + TTL 缓存 |
| `mcp_server/services/parser_service.py` | `ParserService`：直接读取 `output/{type}/{date}.db` SQLite 文件 |
| `mcp_server/services/cache_service.py` | TTL 缓存（哈希 key），减少重复 SQLite 查询 |
| `mcp_server/services/__init__.py` | 包标记 |

### utils/ MCP 工具集

| 文件 | 用途 |
|------|------|
| `mcp_server/utils/errors.py` | `MCPError` 异常体系（`DataNotFoundError` 等） |
| `mcp_server/utils/validators.py` | 参数校验（处理 MCP 客户端传来的字符串化列表/日期） |
| `mcp_server/utils/date_parser.py` | 中英文自然语言日期解析（"本周"、"最近7天"、"last week" 等） |
| `mcp_server/utils/__init__.py` | 包标记 |

---

## 第三部分：docker/ 容器管理

| 文件 | 用途 |
|------|------|
| `docker/manage.py` | **容器管理脚本**：启停内置 Web 服务器（端口 8080，服务 `output/` 目录）、supercronic 定时任务控制、手动触发爬虫 |
| `docker/Dockerfile` | 主应用镜像（trendradar + supercronic + 内置 Web 服务器） |
| `docker/Dockerfile.mcp` | MCP Server 专用镜像 |
| `docker/docker-compose.yml` | 生产 Compose 配置（使用预构建镜像） |
| `docker/docker-compose-build.yml` | 开发 Compose 配置（本地构建镜像） |
| `docker/entrypoint.sh` | 容器启动脚本 |
| `docker/.env` | 环境变量模板（通知、AI、S3、定时任务等） |

**运行命令（Docker）：**

```bash
# 使用预构建镜像启动
cd docker
cp .env .env.local  # 编辑 .env.local 填入配置
docker compose up -d

# 手动触发爬虫（容器内）
docker exec -it <container_name> python manage.py run

# 查看内置 Web 服务器状态
docker exec -it <container_name> python manage.py webserver status
```

**前置条件：**
- Docker 和 Docker Compose 已安装
- `docker/.env` 中填写通知渠道 Webhook URL、AI API Key、S3 配置（如需远程存储）

---

## 第四部分：配置文件

| 文件 | 用途 |
|------|------|
| `config/config.yaml` | **主配置文件**（必须）：平台列表、通知渠道、存储后端、AI 配置、报告模式等 |
| `config/timeline.yaml` | **调度配置**（可选）：定义时间段（早/午/晚），每段的采集/分析/推送行为开关和报告模式 |
| `config/frequency_words.txt` | **关键词配置**（必须）：按分组定义监控词、过滤词、正则规则 |
| `config/ai_interests.txt` | AI 筛选兴趣列表（`FILTER.METHOD=ai` 时使用） |
| `config/ai_analysis_prompt.txt` | AI 分析提示词模板 |
| `config/ai_translation_prompt.txt` | AI 翻译提示词模板 |
| `config/ai_filter/*.txt` | AI 筛选分类提示词 |

---

## 第五部分：项目根目录其他文件

| 文件/目录 | 用途 |
|-----------|------|
| `pyproject.toml` | 项目元数据、依赖声明、构建配置（Hatchling）、CLI 入口点 |
| `requirements.txt` | 固定版本依赖列表（与 `pyproject.toml` 保持一致） |
| `uv.lock` | uv 锁文件（可复现安装） |
| `README.md` | 项目主文档（中文） |
| `README-EN.md` | 项目主文档（英文） |
| `README-MCP-FAQ.md` | MCP Server 常见问题（中文） |
| `README-MCP-FAQ-EN.md` | MCP Server 常见问题（英文） |
| `README-Cherry-Studio.md` | Cherry Studio 集成配置教程 |
| `version` | 主程序版本号（用于远程版本检查） |
| `version_mcp` | MCP Server 版本号 |
| `version_configs` | 配置文件版本清单（格式：`filename=version`） |
| `start-http.sh` / `start-http.bat` | 快捷启动脚本：以 HTTP 模式运行 MCP Server |
| `setup-mac.sh` | macOS 一键安装脚本 |
| `setup-windows.bat` / `setup-windows-en.bat` | Windows 一键安装脚本（中/英文） |
| `index.html` | 项目首页（GitHub Pages） |
| `docs/` | 静态文档站点（`index.html` + CSS + JS） |
| `.github/workflows/` | CI/CD：定时爬虫（crawler.yml）、清理（clean-crawler.yml）、Docker 镜像构建（docker.yml） |

---

## 快速安装

```bash
# 方式一：uv（推荐）
uv sync
python -m trendradar

# 方式二：pip
pip install -e .
python -m trendradar

# 方式三：Docker
cd docker && docker compose up -d
```

---

## 代码规模统计

| 包 | Python 文件数 |
|----|--------------|
| `trendradar/` | 44 |
| `mcp_server/` | 20 |
| `docker/` | 1 |
| **合计** | **65** |
