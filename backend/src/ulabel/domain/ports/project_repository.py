from abc import ABC, abstractmethod
from uuid import UUID

from ulabel.domain.pagination import PaginatedResult
from ulabel.domain.projects import Project


class ProjectRepository(ABC):

    @abstractmethod
    async def get_by_id(self, project_id: UUID) -> Project | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_labeler_id(self, labeler_id: UUID) -> list[Project]:
        raise NotImplementedError

    @abstractmethod
    async def get_all(self, limit: int, offset: int, *, name: str | None = None) -> PaginatedResult[Project]:
        raise NotImplementedError

    @abstractmethod
    async def save(self, project: Project) -> None:
        raise NotImplementedError
