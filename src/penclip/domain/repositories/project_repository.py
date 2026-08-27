"""ProjectRepository interface — abstract persistence for assembly projects."""

from abc import ABC, abstractmethod
from typing import List, Optional

from penclip.domain.entities.assembly_state import AssemblyState


class ProjectRepository(ABC):
    @abstractmethod
    def save(self, project: AssemblyState) -> None:
        ...

    @abstractmethod
    def find_by_id(self, project_id: str) -> Optional[AssemblyState]:
        ...

    @abstractmethod
    def find_by_user(self, user_id: str) -> List[AssemblyState]:
        ...

    @abstractmethod
    def delete(self, project_id: str) -> bool:
        ...

    @abstractmethod
    def update(self, project: AssemblyState) -> None:
        ...
