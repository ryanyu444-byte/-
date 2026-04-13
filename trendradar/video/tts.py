# coding=utf-8
"""
TTS 语音合成模块

基于 edge-tts（微软 Edge 在线 TTS），将文本转为语音音频文件。
支持多语言、多音色，无需 API Key。
"""

import asyncio
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class TTSSegmentResult:
    """单段语音合成结果"""
    segment_id: int = 0
    audio_path: str = ""
    subtitle_path: str = ""
    duration: float = 0.0
    success: bool = False
    error: str = ""


@dataclass
class TTSResult:
    """完整语音合成结果"""
    segments: List[TTSSegmentResult] = field(default_factory=list)
    total_duration: float = 0.0
    success: bool = False
    error: str = ""


class TTSEngine:
    """TTS 语音合成引擎（基于 edge-tts）"""

    VOICE_MAP = {
        "zh-CN-male": "zh-CN-YunxiNeural",
        "zh-CN-female": "zh-CN-XiaoxiaoNeural",
        "zh-CN-news": "zh-CN-YunjianNeural",
        "en-US-male": "en-US-GuyNeural",
        "en-US-female": "en-US-JennyNeural",
        "en-US-news": "en-US-DavisNeural",
        "ja-JP-female": "ja-JP-NanamiNeural",
        "ko-KR-female": "ko-KR-SunHiNeural",
    }

    DEFAULT_VOICES = {
        "Chinese": "zh-CN-YunjianNeural",
        "English": "en-US-DavisNeural",
        "Japanese": "ja-JP-NanamiNeural",
        "Korean": "ko-KR-SunHiNeural",
    }

    def __init__(self, video_config: Dict[str, Any], debug: bool = False):
        self.debug = debug
        tts_config = video_config.get("TTS", {})
        self.voice = tts_config.get("VOICE", "")
        self.rate = tts_config.get("RATE", "+0%")
        self.volume = tts_config.get("VOLUME", "+0%")
        self.pitch = tts_config.get("PITCH", "+0Hz")
        language = video_config.get("LANGUAGE", "Chinese")

        if not self.voice:
            self.voice = self.DEFAULT_VOICES.get(language, "zh-CN-YunjianNeural")

        if self.voice in self.VOICE_MAP:
            self.voice = self.VOICE_MAP[self.voice]

    def synthesize_all(
        self,
        texts: List[Dict[str, str]],
        output_dir: str,
    ) -> TTSResult:
        """
        批量合成语音

        Args:
            texts: [{"id": "opening", "text": "..."}, {"id": "seg_1", "text": "..."}, ...]
            output_dir: 输出目录

        Returns:
            TTSResult
        """
        result = TTSResult()
        os.makedirs(output_dir, exist_ok=True)

        try:
            import edge_tts
        except ImportError:
            result.error = "edge-tts 未安装，请运行: pip install edge-tts"
            return result

        loop = self._get_event_loop()
        segment_results = loop.run_until_complete(
            self._synthesize_batch(texts, output_dir, edge_tts)
        )

        result.segments = segment_results
        result.total_duration = sum(s.duration for s in segment_results if s.success)
        result.success = all(s.success for s in segment_results)
        if not result.success:
            failed = [s for s in segment_results if not s.success]
            result.error = f"{len(failed)} 段语音合成失败"

        return result

    async def _synthesize_batch(
        self,
        texts: List[Dict[str, str]],
        output_dir: str,
        edge_tts,
    ) -> List[TTSSegmentResult]:
        """异步批量合成"""
        results = []
        for i, item in enumerate(texts):
            seg_id = item.get("id", f"seg_{i}")
            text = item.get("text", "")
            if not text.strip():
                results.append(TTSSegmentResult(
                    segment_id=i,
                    success=True,
                    duration=0.0,
                ))
                continue

            audio_path = os.path.join(output_dir, f"{seg_id}.mp3")
            subtitle_path = os.path.join(output_dir, f"{seg_id}.vtt")

            try:
                communicate = edge_tts.Communicate(
                    text,
                    voice=self.voice,
                    rate=self.rate,
                    volume=self.volume,
                    pitch=self.pitch,
                )
                submaker = edge_tts.SubMaker()

                with open(audio_path, "wb") as audio_file:
                    async for chunk in communicate.stream():
                        if chunk["type"] == "audio":
                            audio_file.write(chunk["data"])
                        elif chunk["type"] == "WordBoundary":
                            submaker.feed(chunk)

                if submaker.subs:
                    with open(subtitle_path, "w", encoding="utf-8") as sub_file:
                        sub_file.write(submaker.generate_subs())

                duration = self._get_audio_duration(audio_path)

                results.append(TTSSegmentResult(
                    segment_id=i,
                    audio_path=audio_path,
                    subtitle_path=subtitle_path if os.path.exists(subtitle_path) else "",
                    duration=duration,
                    success=True,
                ))

                if self.debug:
                    print(f"[TTS] {seg_id}: {duration:.1f}s -> {audio_path}")

            except Exception as e:
                error_msg = f"{type(e).__name__}: {str(e)[:100]}"
                results.append(TTSSegmentResult(
                    segment_id=i,
                    error=error_msg,
                ))
                print(f"[TTS] {seg_id} 合成失败: {error_msg}")

        return results

    @staticmethod
    def _get_audio_duration(audio_path: str) -> float:
        """获取音频文件时长"""
        try:
            from mutagen.mp3 import MP3
            audio = MP3(audio_path)
            return audio.info.length
        except Exception:
            file_size = os.path.getsize(audio_path) if os.path.exists(audio_path) else 0
            return file_size / 16000.0

    @staticmethod
    def _get_event_loop():
        """获取或创建事件循环"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop
