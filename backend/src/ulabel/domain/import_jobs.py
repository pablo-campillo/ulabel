"""Domain model for bulk image import jobs."""

from dataclasses import dataclass, field
from enum import StrEnum
from uuid import UUID

from ulabel.domain.errors import DomainError


class ImportJobStatus(StrEnum):
    """Possible lifecycle states of a bulk image import job."""

    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class ImportJobNotFound(DomainError):
    """Raised when a referenced import job does not exist."""

    pass


@dataclass
class ImportJob:
    """Tracks the state and progress of a bulk image import operation.

    Attributes:
        id: Unique identifier for the import job.
        project_id: Identifier of the project images are imported into.
        prefix: Object-storage prefix used to filter which objects to import.
        status: Current lifecycle status of the job.
        imported: Number of images imported so far.
        error: Error message if the job failed, None otherwise.
    """

    id: UUID
    project_id: UUID
    prefix: str
    status: ImportJobStatus
    imported: int = field(default=0)
    error: str | None = field(default=None)

    @classmethod
    def create(cls, id: UUID, project_id: UUID, prefix: str) -> "ImportJob":
        """Create a new import job in RUNNING status.

        Args:
            id: Unique identifier for the job.
            project_id: Identifier of the target project.
            prefix: Object-storage prefix to import from.

        Returns:
            A new ImportJob instance with RUNNING status.
        """
        return cls(id=id, project_id=project_id, prefix=prefix, status=ImportJobStatus.RUNNING)

    def mark_progress(self, count: int) -> None:
        """Record that additional images have been imported.

        Args:
            count: Number of newly imported images to add to the total.
        """
        self.imported += count

    def mark_done(self) -> None:
        """Mark the import job as successfully completed."""
        self.status = ImportJobStatus.DONE

    def mark_failed(self, error: str) -> None:
        """Mark the import job as failed.

        Args:
            error: Description of the error that caused the failure.
        """
        self.status = ImportJobStatus.FAILED
        self.error = error
