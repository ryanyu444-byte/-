# coding=utf-8
"""
TrendRadar 视频创作模块

基于热点新闻数据，利用 AI 生成视频脚本，
结合 TTS 语音合成和 MoviePy 视频渲染，自动生成新闻播报视频。

架构:
    script_writer  → AI 生成视频脚本（旁白 + 字幕 + 分段）
    tts            → 文字转语音（基于 edge-tts）
    renderer       → 视频渲染（基于 MoviePy，合成文字、语音、背景）
    generator      → 编排完整流程（脚本 → 语音 → 视频）
"""

from .generator import VideoGenerator, VideoResult
from .script_writer import VideoScriptWriter, VideoScript
from .tts import TTSEngine
from .renderer import VideoRenderer

__all__ = [
    "VideoGenerator",
    "VideoResult",
    "VideoScriptWriter",
    "VideoScript",
    "TTSEngine",
    "VideoRenderer",
]
