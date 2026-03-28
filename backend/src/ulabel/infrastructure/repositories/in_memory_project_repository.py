from uuid import UUID

from ulabel.domain.pagination import PaginatedResult
from ulabel.domain.ports.project_repository import ProjectRepository
from ulabel.domain.projects import Project


class InMemoryProjectRepository(ProjectRepository):

    def __init__(self, projects: list[Project] | None = None):
        self._projects: dict[UUID, Project] = {p.id: p for p in (projects or [])}

    async def get_by_id(self, project_id: UUID) -> Project | None:
        return self._projects.get(project_id)

    async def get_by_name(self, name: str) -> Project | None:
        for p in self._projects.values():
            if p.name == name:
                return p
        return None

    async def get_by_labeler_id(self, labeler_id: UUID) -> list[Project]:
        return [p for p in self._projects.values() if labeler_id in p.labeler_ids]

    async def get_all(self, limit: int, offset: int, *, name: str | None = None) -> PaginatedResult[Project]:
        all_projects = sorted(
            self._projects.values(),
            key=lambda p: p.created_at,
            reverse=True,
        )
        if name is not None:
            all_projects = [p for p in all_projects if name.lower() in p.name.lower()]
        return PaginatedResult(
            items=all_projects[offset:offset + limit],
            total=len(all_projects),
        )

    async def save(self, project: Project) -> None:
        self._projects[project.id] = project
