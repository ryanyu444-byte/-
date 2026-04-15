# AGENTS.md — Cursor Agent 工作手册

> 这份文档是你的工作说明书。每次接到任务前，先读完再动手。

---

## 一、这是谁的项目

**用户：** Ryan Yu（余晓达），深圳，亚马逊跨境电商卖家 + 小红书内容创作者

**核心业务：**
- 亚马逊美国站销售硅胶胸垫（Sticky Bra / Bra Pads）
- 运营两个亚马逊账号（F 号、N 号）
- 小红书内容运营（带货引流 + 内容变现）
- 目标：月收入 ¥10 万

**你的定位：** 用代码帮他节省时间、提升效率。他不想重复劳动，你负责把重复的事情自动化。

---

## 二、项目结构

```
TrendRadar/                    # 根目录
├── trendradar/                # 核心：热点新闻聚合引擎
│   ├── video/                 # 视频创作模块（AI脚本+TTS+渲染）
│   └── ...
├── mcp_server/                # MCP 服务器（供 AI 助手调用）
│   └── tools/
│       ├── analytics.py       # 数据分析工具
│       ├── notification.py    # 推送（飞书/钉钉/邮件等）
│       ├── search_tools.py    # 新闻搜索
│       ├── video.py           # 视频生成工具
│       └── ...
├── xiaohongshu/               # 小红书内容生成工具（Streamlit 应用）
│   ├── app.py                 # Web UI（streamlit run xiaohongshu/app.py）
│   └── generator.py          # AI 内容生成引擎
├── config/
│   ├── config.yaml            # 主配置文件（API key、关键词、推送渠道）
│   └── frequency_words.txt    # 关键词过滤列表
└── output/                    # 生成的报告和视频
```

---

## 三、常见任务怎么做

### 任务类型 A：修改/新增功能

直接修改对应模块的 Python 文件。注意：
- 代码风格：Python 3.11+，类型注解，中文注释
- 不要破坏已有的 MCP 工具接口（`mcp_server/server.py` 中注册的工具）
- 修改 `config.yaml` 时保留注释，不要删掉说明文字

### 任务类型 B：小红书内容相关

小红书工具在 `xiaohongshu/` 目录：
- `generator.py` — 核心生成逻辑，调用 AI 生成标题/正文/封面文案
- `app.py` — Streamlit UI

如果要改内容风格，修改 `generator.py` 中的 `SYSTEM_PROMPT` 和 `GENERATION_PROMPT`。

**Ryan 的小红书内容方向：**
- 主要话题：内衣收纳/胸型管理/穿搭技巧/硅胶胸垫使用教程
- 风格：真实、有温度、口语化、emoji 适度
- 目标受众：18-35 岁女性

### 任务类型 C：亚马逊业务相关

亚马逊相关脚本在 `amazon/` 目录（如果存在）。

**Ryan 的亚马逊产品：**
- 主品：硅胶胸垫（Sticky Bra / Bra Pads / Nipple Cover）
- 市场：美国站
- 主要 ASIN：B0G61JM8L6（F 号）、B0CTFHB5J5（N 号）

如果任务涉及亚马逊 Listing 优化，重点关注：
1. 标题关键词（sticky bra, adhesive bra, backless bra）
2. Bullet points（卖点：隐形、防水、重复使用、硅胶材质）
3. 图片文案（主图简洁，A+内容丰富）

### 任务类型 D：热点监控 / 内容选题

TrendRadar 监控以下平台：知乎、微博、抖音、bilibili、百度热搜等

常用 MCP 工具：
```python
get_trending_topics()     # 获取当前热榜
search_news(keyword)      # 按关键词搜索新闻
analyze_topic_trend()     # 分析某话题趋势
generate_summary_report() # 生成汇总报告
```

Ryan 关注的关键词方向：
- 内衣/胸垫/胸型/无钢圈/隐形内衣
- 穿搭/ootd/显瘦穿搭
- 跨境电商/亚马逊/选品

---

## 四、配置说明

### API Key 配置

编辑 `config/config.yaml`：

```yaml
ai:
  model: "deepseek/deepseek-chat"   # 或 "anthropic/claude-3-5-sonnet"
  api_key: "你的API_KEY"
```

支持的模型提供商（通过 LiteLLM）：
- DeepSeek：`deepseek/deepseek-chat`（便宜，中文好）
- Claude：`anthropic/claude-sonnet-4-5`
- OpenAI：`openai/gpt-4o`

### 推送渠道配置

`config/config.yaml` 中的 `notification` 段。Ryan 用飞书机器人推送。

---

## 五、运行方式

```bash
# 安装依赖
uv sync

# 运行热点抓取（一次性）
python -m trendradar

# 启动小红书内容生成 Web UI
cd xiaohongshu && streamlit run app.py

# 启动 MCP 服务器（HTTP 模式）
bash start-http.sh

# Docker 方式运行
docker compose up -d
```

---

## 六、如果你不确定要做什么

1. 先读 `config/config.yaml` 了解当前配置
2. 看 `output/` 目录里最新的报告，理解当前输出格式
3. 不要改 `config.yaml` 里的 `api_key`（可能是空的，这是正常的）
4. 改代码前先确认你改的文件是否影响 MCP 接口

---

## 七、注意事项

- **不要提交 API Key 到代码里**，API Key 应该通过 `config.yaml`（本地文件）或环境变量管理
- **不要删除 MCP 工具**，只能新增，删除会导致已配置的 AI 助手失效
- **Python 包管理用 uv**，不要用 pip
- `output/` 目录不提交到 git（已在 .gitignore 中）
