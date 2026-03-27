from uuid import UUID, uuid4

from ulabel.application.login import UserNotFound
from ulabel.domain.ports.project_repository import ProjectRepository
from ulabel.domain.ports.user_repository import UserRepository
from ulabel.domain.projects import Project
from ulabel.domain.users import UserRole


class Unauthorized(Exception):
    pass


class CreateProjectUseCase:

    def __init__(self, user_repository: UserRepository, project_repository: ProjectRepository):
        self.user_repository = user_repository
        self.project_repository = project_repository

    async def execute(self, owner_id: UUID, name: str, description: str, labels: set[str]) -> Project:
        owner = await self.user_repository.get_by_id(owner_id)
        if owner is None:
            raise UserNotFound(f"User '{owner_id}' not found")
        if owner.role != UserRole.ADMIN:
            raise Unauthorized(f"User '{owner.username}' is not an admin")

        project = Project.create(id=uuid4(), owner=owner, name=name, description=description, labels=labels)
        await self.project_repository.save(project)
        return project
