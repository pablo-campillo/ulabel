from uuid import UUID

from ulabel.application.add_labeler_to_project import ProjectNotFound
from ulabel.application.create_project import ProjectNameAlreadyExists, Unauthorized
from ulabel.application.login import UserNotFound
from ulabel.domain.ports.project_repository import ProjectRepository
from ulabel.domain.ports.user_repository import UserRepository
from ulabel.domain.projects import Project
from ulabel.domain.users import UserRole


class UpdateProjectUseCase:

    def __init__(self, user_repository: UserRepository, project_repository: ProjectRepository):
        self.user_repository = user_repository
        self.project_repository = project_repository

    async def execute(
        self,
        project_id: UUID,
        *,
        name: str | None = None,
        description: str | None = None,
        labeler_ids: set[UUID] | None = None,
    ) -> Project:
        project = await self.project_repository.get_by_id(project_id)
        if project is None:
            raise ProjectNotFound("Project not found")

        if name is not None and name != project.name:
            existing = await self.project_repository.get_by_name(name)
            if existing is not None:
                raise ProjectNameAlreadyExists("Project name already exists")

        project.update(name=name, description=description)

        if labeler_ids is not None:
            for labeler_id in labeler_ids:
                user = await self.user_repository.get_by_id(labeler_id)
                if user is None:
                    raise UserNotFound("Labeler not found")
                if user.role != UserRole.LABELER:
                    raise Unauthorized("User is not a labeler")
            project.set_labelers(labeler_ids)

        await self.project_repository.save(project)
        return project
