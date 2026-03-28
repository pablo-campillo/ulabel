from ulabel.domain.pagination import PaginatedResult
from ulabel.domain.ports.project_repository import ProjectRepository
from ulabel.domain.projects import Project


class ListProjectsUseCase:

    def __init__(self, project_repository: ProjectRepository):
        self.project_repository = project_repository

    async def execute(self, limit: int, offset: int, name: str | None = None) -> PaginatedResult[Project]:
        return await self.project_repository.get_all(limit=limit, offset=offset, name=name)
