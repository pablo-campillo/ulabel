from uuid import UUID

from ulabel.application.create_project import Unauthorized
from ulabel.application.login import UserNotFound
from ulabel.domain.errors import DomainError
from ulabel.domain.ports.project_repository import ProjectRepository
from ulabel.domain.ports.user_repository import UserRepository
from ulabel.domain.projects import Project
from ulabel.domain.users import UserRole


class ProjectNotFound(DomainError):
    pass


class AddLabelerToProjectUseCase:

    def __init__(self, user_repository: UserRepository, project_repository: ProjectRepository):
        self.user_repository = user_repository
        self.project_repository = project_repository

    async def execute(self, project_id: UUID, labeler_id: UUID) -> Project:
        project = await self.project_repository.get_by_id(project_id)
        if project is None:
            raise ProjectNotFound("Project not found")

        labeler = await self.user_repository.get_by_id(labeler_id)
        if labeler is None:
            raise UserNotFound("Labeler not found")

        if labeler.role != UserRole.LABELER:
            raise Unauthorized("User is not a labeler")

        project.add_labeler(labeler_id)
        await self.project_repository.save(project)
        return project
