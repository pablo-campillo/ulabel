"""Port interface for import job persistence."""

from abc import ABC, abstractmethod
from uuid import UUID

from ulabel.domain.import_jobs import ImportJob


class ImportJobRepository(ABC):
    """Abstract repository for storing and retrieving import jobs."""

    @abstractmethod
    async def save(self, job: ImportJob) -> None:
        """Persist an import job (insert or update).

        Args:
            job: The import job entity to save.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, job_id: UUID) -> ImportJob | None:
        """Retrieve an import job by its unique identifier.

        Args:
            job_id: The unique identifier of the import job.

        Returns:
            The import job if found, None otherwise.
        """
        raise NotImplementedError
