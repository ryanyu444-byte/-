# coding=utf-8
"""
小红书内容生成引擎

基于 LiteLLM 调用 AI 模型，生成小红书风格的标题、正文和封面文案。
自包含设计，不依赖 trendradar 主包。
"""

import json
from typing import Any, Dict

from litellm import completion

SYSTEM_PROMPT = """你是一位资深的小红书内容创作专家，擅长写出高互动、高收藏的爆款笔记。
你的文风特点：真实、有温度、善用emoji、段落简短、节奏感强。
请严格按照要求的 JSON 格式输出。"""

GENERATION_PROMPT = """请围绕主题「{topic}」，生成一篇完整的小红书笔记内容，包含以下三个部分：

## 要求

### 1. 标题（5个）
- 每个标题 15-25 字
- 包含数字、emoji、悬念或共鸣点
- 风格：口语化、有吸引力、让人想点进来看

### 2. 正文（约800字）
- 开头用 1-2 句 hook 吸引读者（可以是反问、共鸣、数据冲击）
- 正文分 3-5 个小段，每段 2-4 句话
- 适当使用 emoji 增加阅读感
- 结尾引导互动（点赞/收藏/评论）
- 加上 3-5 个相关话题标签（#xxx#）
- 语气：像朋友聊天一样，真实不做作

### 3. 封面文案（1个）
- 6-12 字，适合做封面大字
- 有冲击力、有好奇感
- 简洁明了，能一眼抓住注意力

## 输出格式

请严格按照以下 JSON 格式输出，不要输出任何其他内容：

```json
{{
  "titles": ["标题1", "标题2", "标题3", "标题4", "标题5"],
  "content": "正文内容...",
  "cover_text": "封面文案"
}}
```"""


class XHSClient:
    """小红书生成专用的轻量 AI 客户端"""

    def __init__(self, model: str, api_key: str, api_base: str = ""):
        self.model = model
        self.api_key = api_key
        self.api_base = api_base

    def chat(self, messages: list[Dict[str, str]], **kwargs) -> str:
        params: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.8),
            "timeout": kwargs.get("timeout", 120),
            "num_retries": kwargs.get("num_retries", 2),
            "max_tokens": kwargs.get("max_tokens", 4000),
        }
        if self.api_key:
            params["api_key"] = self.api_key
        if self.api_base:
            params["api_base"] = self.api_base

        response = completion(**params)
        content = response.choices[0].message.content
        if isinstance(content, list):
            content = "\n".join(
                item.get("text", str(item)) if isinstance(item, dict) else str(item)
                for item in content
            )
        return content or ""

    def validate_config(self) -> tuple[bool, str]:
        if not self.model:
            return False, "未配置 AI 模型"
        if not self.api_key:
            return False, "未配置 API Key，请在侧边栏填写"
        if "/" not in self.model:
            return False, f"模型格式错误: {self.model}，应为 'provider/model' 格式（如 'deepseek/deepseek-chat'）"
        return True, ""


def create_client(model: str, api_key: str, api_base: str = "") -> XHSClient:
    """创建 AI 客户端实例"""
    return XHSClient(model=model, api_key=api_key, api_base=api_base)


def generate_content(client: XHSClient, topic: str) -> dict:
    """
    调用 AI 生成小红书内容

    Returns:
        dict: {"titles": [...], "content": "...", "cover_text": "..."}
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": GENERATION_PROMPT.format(topic=topic)},
    ]
    raw = client.chat(messages)
    return _parse_response(raw)


def _parse_response(raw: str) -> dict:
    """
    解析 AI 返回的 JSON 内容。
    兼容模型输出被 markdown 代码块包裹的情况。
    """
    text = raw.strip()

    if "```json" in text:
        text = text.split("```json", 1)[1]
    if "```" in text:
        text = text.split("```", 1)[0]
    text = text.strip()

    try:
        import json_repair
        data = json_repair.loads(text)
    except Exception:
        data = json.loads(text)

    if not isinstance(data, dict):
        raise ValueError("AI 返回格式异常，请重试")

    titles = data.get("titles", [])
    content = data.get("content", "")
    cover_text = data.get("cover_text", "")

    if not titles or not content:
        raise ValueError("AI 返回内容不完整，请重试")

    return {
        "titles": titles[:5],
        "content": content,
        "cover_text": cover_text,
    }
