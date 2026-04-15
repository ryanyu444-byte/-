# coding=utf-8
"""
视频渲染模块

基于 MoviePy，将文本（字幕）和音频合成为视频。
支持纯文字动画风格（无需外部素材），适合自动化生成新闻播报视频。
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from trendradar.video.tts import TTSSegmentResult


@dataclass
class RenderConfig:
    """渲染配置"""
    width: int = 1920
    height: int = 1080
    fps: int = 24
    bg_color: Tuple[int, int, int] = (18, 18, 24)
    title_color: str = "white"
    subtitle_color: str = "#E0E0E0"
    accent_color: str = "#4FC3F7"
    font: str = "Noto-Sans-CJK-SC"
    title_fontsize: int = 64
    subtitle_fontsize: int = 42
    watermark: str = "TrendRadar"


class VideoRenderer:
    """视频渲染器：将字幕 + 音频合成为视频"""

    def __init__(self, video_config: Dict[str, Any], debug: bool = False):
        self.debug = debug
        render_cfg = video_config.get("RENDER", {})
        self.config = RenderConfig(
            width=render_cfg.get("WIDTH", 1920),
            height=render_cfg.get("HEIGHT", 1080),
            fps=render_cfg.get("FPS", 24),
            bg_color=tuple(render_cfg.get("BG_COLOR", [18, 18, 24])),
            title_color=render_cfg.get("TITLE_COLOR", "white"),
            subtitle_color=render_cfg.get("SUBTITLE_COLOR", "#E0E0E0"),
            accent_color=render_cfg.get("ACCENT_COLOR", "#4FC3F7"),
            font=render_cfg.get("FONT", "Noto-Sans-CJK-SC"),
            title_fontsize=render_cfg.get("TITLE_FONTSIZE", 64),
            subtitle_fontsize=render_cfg.get("SUBTITLE_FONTSIZE", 42),
            watermark=render_cfg.get("WATERMARK", "TrendRadar"),
        )

    def render(
        self,
        segments: List[Dict[str, Any]],
        tts_results: List[TTSSegmentResult],
        output_path: str,
        opening_text: str = "",
        closing_text: str = "",
    ) -> Tuple[bool, str]:
        """
        渲染完整视频

        Args:
            segments: 脚本分段 [{"title": ..., "narration": ..., "subtitle": ...}, ...]
            tts_results: TTS 合成结果列表
            output_path: 输出视频路径
            opening_text: 开场白文本
            closing_text: 结尾文本

        Returns:
            (成功与否, 错误信息或输出路径)
        """
        try:
            from moviepy import (
                TextClip,
                CompositeVideoClip,
                AudioFileClip,
                ColorClip,
                concatenate_videoclips,
            )
        except ImportError:
            return False, "moviepy 未安装，请运行: pip install moviepy"

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        try:
            clips = []

            # 开场片段
            if opening_text:
                opening_clip = self._create_text_segment(
                    title="TrendRadar 热点播报",
                    subtitle=opening_text,
                    duration=4.0,
                    audio_path=self._find_tts_audio(tts_results, 0),
                    is_opening=True,
                )
                if opening_clip:
                    clips.append(opening_clip)

            # 内容片段
            tts_offset = 1 if opening_text else 0
            for i, seg in enumerate(segments):
                tts_idx = i + tts_offset
                audio_path = self._find_tts_audio(tts_results, tts_idx)
                duration = self._get_segment_duration(tts_results, tts_idx, seg.get("duration_hint", 5.0))

                clip = self._create_text_segment(
                    title=seg.get("title", f"第{i+1}条"),
                    subtitle=seg.get("subtitle", seg.get("narration", "")),
                    duration=duration,
                    audio_path=audio_path,
                    segment_number=i + 1,
                    total_segments=len(segments),
                )
                if clip:
                    clips.append(clip)

            # 结尾片段
            if closing_text:
                closing_tts_idx = len(segments) + tts_offset
                closing_clip = self._create_text_segment(
                    title="感谢关注",
                    subtitle=closing_text,
                    duration=3.0,
                    audio_path=self._find_tts_audio(tts_results, closing_tts_idx),
                    is_closing=True,
                )
                if closing_clip:
                    clips.append(closing_clip)

            if not clips:
                return False, "没有可渲染的视频片段"

            final = concatenate_videoclips(clips, method="compose")

            print(f"[视频渲染] 正在导出视频: {output_path}")
            print(f"[视频渲染] 总时长: {final.duration:.1f}s, 分辨率: {self.config.width}x{self.config.height}")

            final.write_videofile(
                output_path,
                fps=self.config.fps,
                codec="libx264",
                audio_codec="aac",
                threads=4,
                logger="bar" if self.debug else None,
            )

            for clip in clips:
                clip.close()
            final.close()

            print(f"[视频渲染] 视频生成完成: {output_path}")
            return True, output_path

        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)[:200]}"
            print(f"[视频渲染] 渲染失败: {error_msg}")
            return False, error_msg

    def _create_text_segment(
        self,
        title: str,
        subtitle: str,
        duration: float,
        audio_path: Optional[str] = None,
        segment_number: int = 0,
        total_segments: int = 0,
        is_opening: bool = False,
        is_closing: bool = False,
    ):
        """创建单个文字动画片段"""
        try:
            from moviepy import (
                TextClip,
                CompositeVideoClip,
                AudioFileClip,
                ColorClip,
            )
        except ImportError:
            return None

        actual_duration = duration
        audio_clip = None

        if audio_path and os.path.exists(audio_path):
            try:
                audio_clip = AudioFileClip(audio_path)
                actual_duration = max(duration, audio_clip.duration + 0.5)
            except Exception:
                audio_clip = None

        bg = ColorClip(
            size=(self.config.width, self.config.height),
            color=self.config.bg_color,
        ).with_duration(actual_duration)

        text_clips = [bg]

        if self.config.watermark:
            try:
                wm = TextClip(
                    text=self.config.watermark,
                    font_size=20,
                    color="#555555",
                    font=self.config.font,
                ).with_duration(actual_duration).with_position(("right", "bottom")).with_effects([])
                wm = wm.with_position((self.config.width - 200, self.config.height - 40))
                text_clips.append(wm)
            except Exception:
                pass

        if segment_number > 0 and total_segments > 0:
            try:
                progress_text = f"{segment_number}/{total_segments}"
                progress = TextClip(
                    text=progress_text,
                    font_size=24,
                    color=self.config.accent_color,
                    font=self.config.font,
                ).with_duration(actual_duration).with_position((50, 30))
                text_clips.append(progress)
            except Exception:
                pass

        title_y = self.config.height // 3 if not is_opening else self.config.height // 2 - 60
        try:
            max_title_width = self.config.width - 200
            display_title = self._truncate_text(title, max_chars=30)
            title_clip = TextClip(
                text=display_title,
                font_size=self.config.title_fontsize if not is_opening else 80,
                color=self.config.accent_color if is_opening else self.config.title_color,
                font=self.config.font,
            ).with_duration(actual_duration).with_position(("center", title_y))
            text_clips.append(title_clip)
        except Exception as e:
            if self.debug:
                print(f"[视频渲染] 标题渲染失败: {e}")

        if subtitle:
            subtitle_y = title_y + 100
            try:
                wrapped = self._wrap_text(subtitle, max_chars=28)
                sub_clip = TextClip(
                    text=wrapped,
                    font_size=self.config.subtitle_fontsize,
                    color=self.config.subtitle_color,
                    font=self.config.font,
                    text_align="center",
                ).with_duration(actual_duration).with_position(("center", subtitle_y))
                text_clips.append(sub_clip)
            except Exception as e:
                if self.debug:
                    print(f"[视频渲染] 字幕渲染失败: {e}")

        composite = CompositeVideoClip(text_clips, size=(self.config.width, self.config.height))
        composite = composite.with_duration(actual_duration)

        if audio_clip:
            composite = composite.with_audio(audio_clip)

        return composite

    @staticmethod
    def _find_tts_audio(tts_results: List[TTSSegmentResult], index: int) -> Optional[str]:
        """查找对应索引的 TTS 音频文件"""
        if index < len(tts_results) and tts_results[index].success:
            path = tts_results[index].audio_path
            if path and os.path.exists(path):
                return path
        return None

    @staticmethod
    def _get_segment_duration(
        tts_results: List[TTSSegmentResult],
        index: int,
        fallback: float = 5.0,
    ) -> float:
        """获取片段时长（优先使用 TTS 音频时长）"""
        if index < len(tts_results) and tts_results[index].success:
            return max(tts_results[index].duration + 0.5, 2.0)
        return max(fallback, 2.0)

    @staticmethod
    def _truncate_text(text: str, max_chars: int = 30) -> str:
        """截断过长文本"""
        if len(text) <= max_chars:
            return text
        return text[:max_chars - 1] + "…"

    @staticmethod
    def _wrap_text(text: str, max_chars: int = 28) -> str:
        """将长文本换行"""
        if len(text) <= max_chars:
            return text
        lines = []
        while text:
            if len(text) <= max_chars:
                lines.append(text)
                break
            split_pos = text.rfind("，", 0, max_chars)
            if split_pos == -1:
                split_pos = text.rfind("。", 0, max_chars)
            if split_pos == -1:
                split_pos = text.rfind(" ", 0, max_chars)
            if split_pos == -1:
                split_pos = max_chars
            else:
                split_pos += 1
            lines.append(text[:split_pos])
            text = text[split_pos:]
        return "\n".join(lines)
