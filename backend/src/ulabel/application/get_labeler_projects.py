from uuid import UUID

from ulabel.application.create_project import Unauthorized
from ulabel.application.login import UserNotFound
from ulabel.domain.ports.project_repository import ProjectRepository
from ulabel.domain.ports.user_repository import UserRepository
from ulabel.domain.projects import Project
from ulabel.domain.users import UserRole


class GetLabelerProjectsUseCase:

    def __init__(self, user_repository: UserRepository, project_repository: ProjectRepository):
        self.user_repository = user_repository
        self.project_repository = project_repository

    async def execute(self, labeler_id: UUID) -> list[Project]:
        labeler = await self.user_repository.get_by_id(labeler_id)
        if labeler is None:
            raise UserNotFound(f"User '{labeler_id}' not found")
        if labeler.role != UserRole.LABELER:
            raise Unauthorized(f"User '{labeler.username}' is not a labeler")
        return await self.project_repository.get_by_labeler_id(labeler_id)
