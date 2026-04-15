# 📕 小红书内容生成器

一键生成小红书爆款笔记：输入主题 → 输出 **5 个标题 + 800 字正文 + 封面文案**。

基于 Python + Streamlit + LiteLLM，支持 100+ AI 模型（DeepSeek、OpenAI、Claude 等）。

---

## 功能

| 功能     | 说明                           |
| -------- | ------------------------------ |
| 爆款标题 | 生成 5 个小红书风格标题         |
| 笔记正文 | 约 800 字，带 emoji 和话题标签  |
| 封面文案 | 6-12 字，适合封面大字排版       |
| 一键复制 | 生成结果可直接复制到小红书       |

## 快速开始

### 1. 安装依赖

```bash
pip install -r xiaohongshu/requirements.txt
```

### 2. 运行

```bash
streamlit run xiaohongshu/app.py
```

浏览器会自动打开 `http://localhost:8501`。

### 3. 配置

在页面左侧边栏填写：

- **模型名称**：LiteLLM 格式，如 `deepseek/deepseek-chat`、`openai/gpt-4o`
- **API Key**：对应模型提供商的密钥
- **API Base URL**（可选）：自定义接口地址

### 4. 使用

1. 在主区域输入笔记主题（如「大学生高效学习方法」）
2. 点击「✨ 一键生成内容」
3. 等待 15-30 秒，查看生成结果
4. 复制标题 / 正文 / 封面文案到小红书发布

## 支持的 AI 模型

通过 [LiteLLM](https://docs.litellm.ai/docs/providers)，支持 100+ 提供商：

| 提供商   | 模型名称示例                          |
| -------- | ------------------------------------- |
| DeepSeek | `deepseek/deepseek-chat`              |
| OpenAI   | `openai/gpt-4o`、`openai/gpt-4o-mini`|
| Anthropic| `anthropic/claude-3-5-sonnet-20241022`|
| 智谱     | `zhipu/glm-4-flash`                  |

也可以使用 `openai/xxx` + 自定义 Base URL 接入任意 OpenAI 兼容接口。

## 项目结构

```
xiaohongshu/
├── app.py              # Streamlit 主应用
├── generator.py        # 内容生成引擎（调用 AI）
├── requirements.txt    # 依赖
└── README.md           # 说明文档
```

## 技术栈

- **Python 3.12+**
- **Streamlit** — Web UI 框架
- **LiteLLM** — 统一 AI 模型调用
- **json-repair** — 容错 JSON 解析
