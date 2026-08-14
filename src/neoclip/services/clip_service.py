"""CLIPService — wrapper for CLIP-based zero-shot image classification."""

from typing import Any, Dict, List, Optional

from neoclip.logger import debug


class CLIPService:
    """V0.1 stub — delegates to external CLIP model in V0.2."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._config = config or {}
        debug("CLIPService initialized (stub)")

    def classify(self, image_path: str, labels: List[str]) -> Dict[str, float]:
        return {label: 0.0 for label in labels}

    def embed_image(self, image_path: str) -> List[float]:
        return []

    def embed_text(self, text: str) -> List[float]:
        return []
