"""Use case for listing labeling projects with pagination and optional filtering."""

from ulabel.domain.pagination import PaginatedResult
from ulabel.domain.ports.project_repository import ProjectRepository
from ulabel.domain.projects import Project


class ListProjectsUseCase:
    """Lists projects with pagination and optional name filtering."""

    def __init__(self, project_repository: ProjectRepository):
        """Initialize the use case.

        Args:
            project_repository: Repository for project queries.
        """
        self.project_repository = project_repository

    async def execute(
        self,
        limit: int,
        offset: int,
        name: str | None = None,
    ) -> PaginatedResult[Project]:
        """List projects with pagination.

        Args:
            limit: Maximum number of projects to return.
            offset: Number of projects to skip.
            name: Optional name filter for partial matching.

        Returns:
            A paginated result containing the matching projects.
        """
        return await self.project_repository.get_all(limit=limit, offset=offset, name=name)
