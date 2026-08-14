"""Service layer — abstract interfaces and implementations for external tools."""

from neoclip.services.llm_service import LLMService, LLMFactory
from neoclip.services.clip_service import CLIPService
from neoclip.services.ffmpeg_service import FFmpegService
from neoclip.services.scene_detect_service import SceneDetectService
from neoclip.services.vector_service import VectorService
from neoclip.services.file_service import FileService

__all__ = [
    "LLMService", "LLMFactory",
    "CLIPService",
    "FFmpegService",
    "SceneDetectService",
    "VectorService",
    "FileService",
]
