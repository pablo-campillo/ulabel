"""Use case for assigning a labeler to a labeling project."""

from uuid import UUID

from ulabel.application.create_project import Unauthorized
from ulabel.application.login import UserNotFound
from ulabel.domain.errors import DomainError
from ulabel.domain.ports.project_repository import ProjectRepository
from ulabel.domain.ports.user_repository import UserRepository
from ulabel.domain.projects import Project
from ulabel.domain.users import UserRole


class ProjectNotFound(DomainError):
    """Raised when a referenced project does not exist."""

    pass


class AddLabelerToProjectUseCase:
    """Adds a labeler user to a project so they can receive assignments.

    Validates that both the project and labeler exist, and that the user
    holds the labeler role.
    """

    def __init__(self, user_repository: UserRepository, project_repository: ProjectRepository):
        """Initialize the use case.

        Args:
            user_repository: Repository for user lookups.
            project_repository: Repository for project lookups and persistence.
        """
        self.user_repository = user_repository
        self.project_repository = project_repository

    async def execute(self, project_id: UUID, labeler_id: UUID) -> Project:
        """Add a labeler to a project.

        Args:
            project_id: The ID of the target project.
            labeler_id: The ID of the user to add as a labeler.

        Returns:
            The updated project entity with the labeler added.

        Raises:
            ProjectNotFound: If the project does not exist.
            UserNotFound: If the labeler user does not exist.
            Unauthorized: If the user does not have the labeler role.
        """
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
