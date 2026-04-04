"""Use case for retrieving a single project with resolved labeler details."""

from uuid import UUID

from ulabel.application.add_labeler_to_project import ProjectNotFound
from ulabel.application.dtos import ProjectWithLabelers, ResolvedLabeler
from ulabel.domain.ports.project_repository import ProjectRepository
from ulabel.domain.ports.user_repository import UserRepository


class GetProjectUseCase:
    """Retrieves a project by ID with fully resolved labeler information.

    Uses a batch query to resolve all labeler usernames in a single
    database round-trip.
    """

    def __init__(self, project_repository: ProjectRepository, user_repository: UserRepository):
        """Initialize the use case.

        Args:
            project_repository: Repository for project persistence.
            user_repository: Repository for user lookups.
        """
        self.project_repository = project_repository
        self.user_repository = user_repository

    async def execute(self, project_id: UUID) -> ProjectWithLabelers:
        """Retrieve a project with resolved labeler details.

        Args:
            project_id: The unique identifier of the project.

        Returns:
            A ProjectWithLabelers containing the project and its resolved labelers.

        Raises:
            ProjectNotFound: If no project exists with the given ID.
        """
        project = await self.project_repository.get_by_id(project_id)
        if project is None:
            raise ProjectNotFound()

        users = await self.user_repository.get_by_ids(project.labeler_ids)
        users_by_id = {u.id: u for u in users}

        labelers = [
            ResolvedLabeler(
                id=lid,
                username=users_by_id[lid].username if lid in users_by_id else str(lid),
            )
            for lid in project.labeler_ids
        ]

        return ProjectWithLabelers(project=project, labelers=labelers)
