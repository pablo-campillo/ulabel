"""Use case for creating a new labeling project."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from ulabel.application.login import UserNotFound
from ulabel.domain.errors import DomainError
from ulabel.domain.ports.project_repository import ProjectRepository
from ulabel.domain.ports.user_repository import UserRepository
from ulabel.domain.projects import Project
from ulabel.domain.users import UserRole


class Unauthorized(DomainError):
    """Raised when a user lacks the required role for an operation."""

    pass


class ProjectNameAlreadyExists(DomainError):
    """Raised when a project name is already taken."""

    pass


class CreateProjectUseCase:
    """Creates a new labeling project owned by an admin user.

    Validates that the owner exists and has admin privileges, and that
    the project name is unique.
    """

    def __init__(self, user_repository: UserRepository, project_repository: ProjectRepository):
        """Initialize the use case.

        Args:
            user_repository: Repository for user lookups.
            project_repository: Repository for project lookups and persistence.
        """
        self.user_repository = user_repository
        self.project_repository = project_repository

    async def execute(
        self,
        owner_id: UUID,
        name: str,
        description: str,
        labels: set[str],
    ) -> Project:
        """Create a new labeling project.

        Args:
            owner_id: The ID of the admin user who will own the project.
            name: The unique display name for the project.
            description: A brief description of the project.
            labels: The set of allowed label values for the project.

        Returns:
            The newly created project entity.

        Raises:
            UserNotFound: If the owner user does not exist.
            Unauthorized: If the owner is not an admin.
            ProjectNameAlreadyExists: If a project with the given name already exists.
        """
        owner = await self.user_repository.get_by_id(owner_id)
        if owner is None:
            raise UserNotFound("Owner not found")
        if owner.role != UserRole.ADMIN:
            raise Unauthorized("Owner is not an admin")

        existing = await self.project_repository.get_by_name(name)
        if existing is not None:
            raise ProjectNameAlreadyExists("Project name already exists")

        project = Project.create(
            id=uuid4(),
            owner=owner,
            name=name,
            description=description,
            labels=labels,
            created_at=datetime.now(timezone.utc),
        )
        await self.project_repository.save(project)
        return project
