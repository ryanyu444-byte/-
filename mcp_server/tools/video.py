# coding=utf-8
"""
视频生成工具

通过 MCP 接口触发视频生成，查询生成状态和已生成的视频列表。
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from ..utils.errors import MCPError, InvalidParameterError


class VideoTools:
    """视频生成相关的 MCP 工具"""

    def __init__(self, project_root: Optional[str] = None):
        self.project_root = project_root or self._detect_project_root()

    def _detect_project_root(self) -> str:
        """检测项目根目录"""
        candidates = [
            os.environ.get("TRENDRADAR_ROOT", ""),
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            os.getcwd(),
        ]
        for path in candidates:
            if path and os.path.exists(os.path.join(path, "config", "config.yaml")):
                return path
        return os.getcwd()

    def list_videos(
        self,
        date: Optional[str] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        列出已生成的视频文件

        Args:
            date: 指定日期 (YYYY-MM-DD)，为空则列出所有
            limit: 最多返回数量

        Returns:
            视频文件列表
        """
        video_dir = self._get_video_dir()
        if not os.path.exists(video_dir):
            return {"videos": [], "total": 0, "message": "暂无视频文件"}

        videos = []

        if date:
            date_dir = os.path.join(video_dir, date)
            if os.path.exists(date_dir):
                videos.extend(self._scan_video_dir(date_dir, date))
        else:
            for entry in sorted(os.listdir(video_dir), reverse=True):
                entry_path = os.path.join(video_dir, entry)
                if os.path.isdir(entry_path) and entry not in ("temp", "latest"):
                    videos.extend(self._scan_video_dir(entry_path, entry))
                    if len(videos) >= limit:
                        break

        videos = videos[:limit]
        return {
            "videos": videos,
            "total": len(videos),
        }

    def get_video_config(self) -> Dict[str, Any]:
        """获取当前视频生成配置"""
        config_path = os.path.join(self.project_root, "config", "config.yaml")
        if not os.path.exists(config_path):
            raise MCPError("配置文件不存在")

        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)

        video_config = config_data.get("video", {})
        return {
            "enabled": video_config.get("enabled", False),
            "language": video_config.get("language", "Chinese"),
            "style": video_config.get("style", "professional"),
            "max_segments": video_config.get("max_segments", 8),
            "output_dir": video_config.get("output_dir", "output/video"),
            "tts_voice": video_config.get("tts", {}).get("voice", "auto"),
            "resolution": f"{video_config.get('render', {}).get('width', 1920)}x{video_config.get('render', {}).get('height', 1080)}",
        }

    def get_latest_video(self) -> Dict[str, Any]:
        """获取最新生成的视频信息"""
        video_dir = self._get_video_dir()
        latest_path = os.path.join(video_dir, "latest", "latest.mp4")

        if os.path.exists(latest_path):
            stat = os.stat(latest_path)
            return {
                "path": latest_path,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "modified": os.path.getmtime(latest_path),
                "exists": True,
            }
        return {"exists": False, "message": "暂无已生成的视频"}

    def _get_video_dir(self) -> str:
        """获取视频输出目录"""
        config_path = os.path.join(self.project_root, "config", "config.yaml")
        video_dir = "output/video"
        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    config_data = yaml.safe_load(f)
                video_dir = config_data.get("video", {}).get("output_dir", video_dir)
        except Exception:
            pass
        return os.path.join(self.project_root, video_dir)

    def _scan_video_dir(self, dir_path: str, date_label: str) -> List[Dict]:
        """扫描目录中的视频文件"""
        videos = []
        for fname in sorted(os.listdir(dir_path), reverse=True):
            if fname.endswith(".mp4"):
                fpath = os.path.join(dir_path, fname)
                stat = os.stat(fpath)
                videos.append({
                    "date": date_label,
                    "filename": fname,
                    "path": fpath,
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "modified": stat.st_mtime,
                })
        return videos
