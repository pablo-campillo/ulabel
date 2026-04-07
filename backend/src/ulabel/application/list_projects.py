"""Use case for listing labeling projects with pagination and optional filtering."""

from ulabel.domain.pagination import PaginatedResult
from ulabel.domain.ports.unit_of_work import UnitOfWork
from ulabel.domain.projects import Project


class ListProjectsUseCase:
    """Lists projects with pagination and optional name filtering."""

    def __init__(self, uow: UnitOfWork):
        """Initialize the use case.

        Args:
            uow: Unit of Work for transactional repository access.
        """
        self._uow = uow

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
        async with self._uow as uow:
            return await uow.project_repository.get_all(limit=limit, offset=offset, name=name)
