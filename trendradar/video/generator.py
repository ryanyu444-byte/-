# coding=utf-8
"""
视频生成器模块

编排完整的视频生成流程：
    1. AI 生成视频脚本
    2. TTS 语音合成
    3. MoviePy 视频渲染
    4. 输出最终视频文件
"""

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from trendradar.video.script_writer import VideoScriptWriter, VideoScript
from trendradar.video.tts import TTSEngine, TTSResult
from trendradar.video.renderer import VideoRenderer


@dataclass
class VideoResult:
    """视频生成结果"""
    video_path: str = ""
    script: Optional[VideoScript] = None
    tts_result: Optional[TTSResult] = None
    duration: float = 0.0
    success: bool = False
    error: str = ""
    skipped: bool = False


class VideoGenerator:
    """视频生成器：编排脚本→语音→渲染的完整流程"""

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

        self.enabled = video_config.get("ENABLED", False)
        self.output_dir = video_config.get("OUTPUT_DIR", "output/video")
        self.keep_temp = video_config.get("KEEP_TEMP", False)

        self.script_writer = VideoScriptWriter(
            ai_config=ai_config,
            video_config=video_config,
            get_time_func=get_time_func,
            debug=debug,
        )
        self.tts_engine = TTSEngine(video_config=video_config, debug=debug)
        self.renderer = VideoRenderer(video_config=video_config, debug=debug)

    def generate(
        self,
        stats: List[Dict],
        rss_stats: Optional[List[Dict]] = None,
        report_mode: str = "daily",
        report_type: str = "热点播报",
        ai_analysis: Optional[Any] = None,
        date_folder: str = "",
    ) -> VideoResult:
        """
        执行完整的视频生成流程

        Args:
            stats: 热榜统计数据
            rss_stats: RSS 统计数据
            report_mode: 报告模式
            report_type: 报告类型
            ai_analysis: AI 分析结果
            date_folder: 日期文件夹名

        Returns:
            VideoResult
        """
        if not self.enabled:
            return VideoResult(skipped=True, error="视频生成功能未启用")

        if not stats:
            return VideoResult(skipped=True, error="无新闻数据可用于生成视频")

        print("[视频] === 开始视频生成流程 ===")

        # Step 1: 生成脚本
        print("[视频] Step 1/3: 生成视频脚本...")
        script = self.script_writer.generate_script(
            stats=stats,
            rss_stats=rss_stats,
            report_mode=report_mode,
            report_type=report_type,
            ai_analysis=ai_analysis,
        )

        if not script.success:
            print(f"[视频] 脚本生成失败: {script.error}")
            return VideoResult(
                script=script,
                success=False,
                error=f"脚本生成失败: {script.error}",
            )

        print(f"[视频] 脚本生成完成: {len(script.segments)} 个片段")

        # Step 2: TTS 语音合成
        print("[视频] Step 2/3: 语音合成...")
        video_date = date_folder or self.get_time_func().strftime("%Y-%m-%d")
        temp_dir = os.path.join(self.output_dir, "temp", video_date)
        os.makedirs(temp_dir, exist_ok=True)

        tts_texts = self._build_tts_texts(script)
        tts_result = self.tts_engine.synthesize_all(tts_texts, temp_dir)

        if not tts_result.success:
            print(f"[视频] 语音合成部分失败: {tts_result.error}")
            # TTS 部分失败不阻断流程，使用静音段替代

        print(f"[视频] 语音合成完成: 总时长 {tts_result.total_duration:.1f}s")

        # Step 3: 视频渲染
        print("[视频] Step 3/3: 视频渲染...")
        time_str = self.get_time_func().strftime("%H-%M")
        video_dir = os.path.join(self.output_dir, video_date)
        os.makedirs(video_dir, exist_ok=True)
        output_path = os.path.join(video_dir, f"trendradar_{time_str}.mp4")

        segments_data = [
            {
                "title": seg.title,
                "narration": seg.narration,
                "subtitle": seg.subtitle or seg.narration,
                "duration_hint": seg.duration_hint,
            }
            for seg in script.segments
        ]

        ok, result_info = self.renderer.render(
            segments=segments_data,
            tts_results=tts_result.segments,
            output_path=output_path,
            opening_text=script.opening,
            closing_text=script.closing,
        )

        if not self.keep_temp and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass

        # 更新 latest 软链接
        if ok:
            self._update_latest_link(output_path)

        result = VideoResult(
            video_path=output_path if ok else "",
            script=script,
            tts_result=tts_result,
            duration=tts_result.total_duration,
            success=ok,
            error="" if ok else result_info,
        )

        if ok:
            print(f"[视频] === 视频生成完成 ===")
            print(f"[视频] 输出: {output_path}")
            print(f"[视频] 时长: {tts_result.total_duration:.1f}s")
            print(f"[视频] 片段: {len(script.segments)}")
        else:
            print(f"[视频] === 视频生成失败 ===")
            print(f"[视频] 错误: {result_info}")

        return result

    def _build_tts_texts(self, script: VideoScript) -> List[Dict[str, str]]:
        """构建 TTS 合成文本列表"""
        texts = []

        if script.opening:
            texts.append({"id": "opening", "text": script.opening})

        for seg in script.segments:
            texts.append({
                "id": f"seg_{seg.segment_id}",
                "text": seg.narration,
            })

        if script.closing:
            texts.append({"id": "closing", "text": script.closing})

        return texts

    def _update_latest_link(self, video_path: str) -> None:
        """更新 latest 目录下的最新视频链接"""
        latest_dir = os.path.join(self.output_dir, "latest")
        os.makedirs(latest_dir, exist_ok=True)
        latest_path = os.path.join(latest_dir, "latest.mp4")

        try:
            if os.path.exists(latest_path) or os.path.islink(latest_path):
                os.remove(latest_path)
            shutil.copy2(video_path, latest_path)
        except Exception as e:
            if self.debug:
                print(f"[视频] 更新 latest 链接失败: {e}")
