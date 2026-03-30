"""Use case for retrieving all projects assigned to a labeler."""

from uuid import UUID

from ulabel.application.create_project import Unauthorized
from ulabel.application.login import UserNotFound
from ulabel.domain.ports.project_repository import ProjectRepository
from ulabel.domain.ports.user_repository import UserRepository
from ulabel.domain.projects import Project
from ulabel.domain.users import UserRole


class GetLabelerProjectsUseCase:
    """Retrieves the list of projects a labeler is assigned to.

    Validates that the user exists and holds the labeler role.
    """

    def __init__(self, user_repository: UserRepository, project_repository: ProjectRepository):
        """Initialize the use case.

        Args:
            user_repository: Repository for user lookups.
            project_repository: Repository for project lookups.
        """
        self.user_repository = user_repository
        self.project_repository = project_repository

    async def execute(self, labeler_id: UUID) -> list[Project]:
        """Get all projects for a labeler.

        Args:
            labeler_id: The ID of the labeler user.

        Returns:
            A list of projects the labeler is assigned to.

        Raises:
            UserNotFound: If the labeler user does not exist.
            Unauthorized: If the user does not have the labeler role.
        """
        labeler = await self.user_repository.get_by_id(labeler_id)
        if labeler is None:
            raise UserNotFound("Labeler not found")
        if labeler.role != UserRole.LABELER:
            raise Unauthorized("User is not a labeler")
        return await self.project_repository.get_by_labeler_id(labeler_id)
