"""AssetRepository interface — abstract persistence for video assets."""

from abc import ABC, abstractmethod
from typing import List, Optional

from penclip.domain.entities.video_asset import VideoAsset


class AssetRepository(ABC):
    @abstractmethod
    def save(self, asset: VideoAsset) -> None:
        ...

    @abstractmethod
    def find_by_id(self, asset_id: str) -> Optional[VideoAsset]:
        ...

    @abstractmethod
    def find_by_session(self, session_id: str) -> List[VideoAsset]:
        ...

    @abstractmethod
    def delete(self, asset_id: str) -> bool:
        ...

    @abstractmethod
    def exists(self, file_hash: str) -> bool:
        ...
