"""Port interface for project persistence."""

from abc import ABC, abstractmethod
from uuid import UUID

from ulabel.domain.pagination import PaginatedResult
from ulabel.domain.projects import Project


class ProjectRepository(ABC):
    """Abstract repository for storing and retrieving projects."""

    @abstractmethod
    async def get_by_id(self, project_id: UUID) -> Project | None:
        """Retrieve a project by its unique identifier.

        Args:
            project_id: The unique identifier of the project.

        Returns:
            The project if found, None otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_by_name(self, name: str) -> Project | None:
        """Retrieve a project by its name.

        Args:
            name: The exact project name to search for.

        Returns:
            The project if found, None otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_by_labeler_id(self, labeler_id: UUID) -> list[Project]:
        """Retrieve all projects assigned to a given labeler.

        Args:
            labeler_id: The identifier of the labeler.

        Returns:
            A list of projects the labeler is assigned to.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_all(self, limit: int, offset: int, *, name: str | None = None) -> PaginatedResult[Project]:
        """Retrieve a paginated list of projects, optionally filtered by name.

        Args:
            limit: Maximum number of projects to return.
            offset: Number of projects to skip.
            name: Optional name filter (substring or prefix match).

        Returns:
            A paginated result containing the matching projects.
        """
        raise NotImplementedError

    @abstractmethod
    async def save(self, project: Project) -> None:
        """Persist a project (insert or update).

        Args:
            project: The project entity to save.
        """
        raise NotImplementedError
