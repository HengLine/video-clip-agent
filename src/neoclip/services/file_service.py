"""FileService — file system operations (upload, read, delete)."""

import os
from typing import Any, BinaryIO, Dict, Optional

from neoclip.logger import debug


class FileService:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._config = config or {}
        self._base_dir = self._config.get("base_dir", "data")
        debug(f"FileService initialized (base_dir={self._base_dir})")

    def save(self, filename: str, data: bytes) -> str:
        path = os.path.join(self._base_dir, filename)
        os.makedirs(os.path.dirname(path) or self._base_dir, exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
        return path

    def read(self, path: str) -> bytes:
        with open(path, "rb") as f:
            return f.read()

    def delete(self, path: str) -> bool:
        try:
            os.remove(path)
            return True
        except OSError:
            return False

    def exists(self, path: str) -> bool:
        return os.path.exists(path)
