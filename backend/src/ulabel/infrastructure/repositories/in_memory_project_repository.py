from uuid import UUID

from ulabel.domain.ports.project_repository import ProjectRepository
from ulabel.domain.projects import Project


class InMemoryProjectRepository(ProjectRepository):

    def __init__(self, projects: list[Project] | None = None):
        self._projects: dict[UUID, Project] = {p.id: p for p in (projects or [])}

    async def get_by_id(self, project_id: UUID) -> Project | None:
        return self._projects.get(project_id)

    async def get_by_labeler_id(self, labeler_id: UUID) -> list[Project]:
        return [p for p in self._projects.values() if labeler_id in p.labeler_ids]

    async def save(self, project: Project) -> None:
        self._projects[project.id] = project
