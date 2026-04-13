# coding=utf-8
"""
视频脚本生成模块

调用 AI 大模型将热点新闻数据转化为结构化的视频脚本，
包含分段旁白、字幕文本和时长建议。
"""

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from trendradar.ai.client import AIClient
from trendradar.ai.prompt_loader import load_prompt_template


@dataclass
class ScriptSegment:
    """视频脚本片段"""
    segment_id: int = 0
    title: str = ""
    narration: str = ""
    subtitle: str = ""
    duration_hint: float = 5.0
    keywords: List[str] = field(default_factory=list)


@dataclass
class VideoScript:
    """完整视频脚本"""
    opening: str = ""
    segments: List[ScriptSegment] = field(default_factory=list)
    closing: str = ""
    total_duration_hint: float = 0.0
    raw_response: str = ""
    success: bool = False
    error: str = ""


class VideoScriptWriter:
    """视频脚本生成器：调用 AI 将新闻数据转化为播报脚本"""

    def __init__(
        self,
        ai_config: Dict[str, Any],
        video_config: Dict[str, Any],
        get_time_func: Callable,
        debug: bool = False,
    ):
        self.ai_config = ai_config
        self.video_config = video_config
        self.get_time_func = get_time_func
        self.debug = debug

        self.client = AIClient(ai_config)

        valid, error = self.client.validate_config()
        if not valid:
            print(f"[视频脚本] 配置警告: {error}")

        self.language = video_config.get("LANGUAGE", "Chinese")
        self.max_segments = video_config.get("MAX_SEGMENTS", 8)
        self.style = video_config.get("STYLE", "professional")

        self.system_prompt, self.user_prompt_template = load_prompt_template(
            video_config.get("SCRIPT_PROMPT_FILE", "video_script_prompt.txt"),
            label="视频脚本",
        )

    def generate_script(
        self,
        stats: List[Dict],
        rss_stats: Optional[List[Dict]] = None,
        report_mode: str = "daily",
        report_type: str = "热点播报",
        ai_analysis: Optional[Any] = None,
    ) -> VideoScript:
        """
        生成视频脚本

        Args:
            stats: 热榜统计数据
            rss_stats: RSS 统计数据
            report_mode: 报告模式
            report_type: 报告类型
            ai_analysis: AI 分析结果（可选，用于增强脚本深度）

        Returns:
            VideoScript: 生成的视频脚本
        """
        if not self.client.api_key:
            return VideoScript(
                success=False,
                error="未配置 AI API Key"
            )

        news_content = self._prepare_news_content(stats, rss_stats)
        if not news_content:
            return VideoScript(
                success=False,
                error="无新闻内容可用于生成视频脚本"
            )

        current_time = self.get_time_func().strftime("%Y-%m-%d %H:%M")

        analysis_summary = ""
        if ai_analysis and hasattr(ai_analysis, "core_trends") and ai_analysis.core_trends:
            analysis_summary = ai_analysis.core_trends[:500]

        user_prompt = self.user_prompt_template
        user_prompt = user_prompt.replace("{current_time}", current_time)
        user_prompt = user_prompt.replace("{report_mode}", report_mode)
        user_prompt = user_prompt.replace("{report_type}", report_type)
        user_prompt = user_prompt.replace("{news_content}", news_content)
        user_prompt = user_prompt.replace("{max_segments}", str(self.max_segments))
        user_prompt = user_prompt.replace("{language}", self.language)
        user_prompt = user_prompt.replace("{style}", self.style)
        user_prompt = user_prompt.replace("{analysis_summary}", analysis_summary)

        if self.debug:
            print(f"[视频脚本] 发送 AI 请求...")
            print(f"[视频脚本] 新闻内容长度: {len(news_content)} 字符")

        try:
            messages = []
            if self.system_prompt:
                messages.append({"role": "system", "content": self.system_prompt})
            messages.append({"role": "user", "content": user_prompt})

            response = self.client.chat(messages)
            script = self._parse_response(response)
            return script
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            if len(error_msg) > 200:
                error_msg = error_msg[:200] + "..."
            return VideoScript(
                success=False,
                error=f"脚本生成失败 ({error_type}): {error_msg}"
            )

    def _prepare_news_content(
        self,
        stats: List[Dict],
        rss_stats: Optional[List[Dict]] = None,
    ) -> str:
        """将新闻统计数据转为文本供 AI 使用"""
        lines = []
        count = 0
        max_items = self.max_segments * 5

        if stats:
            for stat in stats:
                word = stat.get("word", "")
                titles = stat.get("titles", [])
                if word and titles:
                    lines.append(f"\n**{word}** ({len(titles)}条)")
                    for t in titles:
                        if not isinstance(t, dict):
                            continue
                        title = t.get("title", "")
                        if not title:
                            continue
                        source = t.get("source_name", t.get("source", ""))
                        if source:
                            lines.append(f"- [{source}] {title}")
                        else:
                            lines.append(f"- {title}")
                        count += 1
                        if count >= max_items:
                            break
                if count >= max_items:
                    break

        if rss_stats:
            remaining = max_items - count
            if remaining > 0:
                lines.append("\n--- RSS ---")
                rss_count = 0
                for stat in rss_stats:
                    word = stat.get("word", "")
                    titles = stat.get("titles", [])
                    if word and titles:
                        lines.append(f"\n**{word}** ({len(titles)}条)")
                        for t in titles:
                            if not isinstance(t, dict):
                                continue
                            title = t.get("title", "")
                            if not title:
                                continue
                            source = t.get("source_name", t.get("feed_name", ""))
                            if source:
                                lines.append(f"- [{source}] {title}")
                            else:
                                lines.append(f"- {title}")
                            rss_count += 1
                            if rss_count >= remaining:
                                break
                    if rss_count >= remaining:
                        break

        return "\n".join(lines) if lines else ""

    def _parse_response(self, response: str) -> VideoScript:
        """解析 AI 返回的视频脚本 JSON"""
        script = VideoScript(raw_response=response)

        if not response or not response.strip():
            script.error = "AI 返回空响应"
            return script

        json_str = response
        if "```json" in response:
            parts = response.split("```json", 1)
            if len(parts) > 1:
                code_block = parts[1]
                end_idx = code_block.find("```")
                if end_idx != -1:
                    json_str = code_block[:end_idx]
                else:
                    json_str = code_block
        elif "```" in response:
            parts = response.split("```", 2)
            if len(parts) >= 2:
                json_str = parts[1]

        json_str = json_str.strip()

        data = None
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            try:
                from json_repair import repair_json
                repaired = repair_json(json_str, return_objects=True)
                if isinstance(repaired, dict):
                    data = repaired
            except Exception:
                pass

        if data is None:
            script.error = "JSON 解析失败"
            script.opening = json_str[:300] + "..." if len(json_str) > 300 else json_str
            script.success = True
            return script

        try:
            script.opening = data.get("opening", "")
            script.closing = data.get("closing", "")

            segments_data = data.get("segments", [])
            for i, seg in enumerate(segments_data):
                segment = ScriptSegment(
                    segment_id=i + 1,
                    title=seg.get("title", ""),
                    narration=seg.get("narration", ""),
                    subtitle=seg.get("subtitle", seg.get("title", "")),
                    duration_hint=float(seg.get("duration_hint", 5.0)),
                    keywords=seg.get("keywords", []),
                )
                script.segments.append(segment)

            script.total_duration_hint = (
                sum(s.duration_hint for s in script.segments) + 5.0 + 3.0
            )
            script.success = True
        except (KeyError, TypeError, ValueError) as e:
            script.error = f"脚本字段解析错误: {e}"
            script.success = True

        return script
