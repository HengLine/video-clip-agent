"""FFmpegService — unified interface for FFmpeg operations."""

from typing import Any, Dict, List, Optional

from neoclip.logger import debug, info


class FFmpegService:
    """V0.1 wrapper — delegates to neoclip.utils.ffmpeg_* modules for actual execution."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._config = config or {}
        debug("FFmpegService initialized")

    def cut_segment(self, input_path: str, start: float, end: float, output_path: str) -> bool:
        from neoclip.utils.ffmpeg_utils import build_cut_command
        from neoclip.utils.ffmpeg_run_utils import run_ffmpeg_command

        cmd = build_cut_command(input_path, start, end, output_path)
        return run_ffmpeg_command(cmd)

    def concat_clips(self, clip_paths: List[str], output_path: str, transition: Optional[str] = None) -> bool:
        from neoclip.utils.ffmpeg_utils import build_concat_command
        from neoclip.utils.ffmpeg_run_utils import run_ffmpeg_command

        cmd = build_concat_command(clip_paths, output_path, transition)
        return run_ffmpeg_command(cmd)

    def get_metadata(self, video_path: str) -> Dict[str, Any]:
        from neoclip.utils.ffmpeg_run_utils import get_video_metadata
        return get_video_metadata(video_path)
