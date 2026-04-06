"""In-memory implementation of the import job repository for testing."""

from uuid import UUID

from ulabel.domain.import_jobs import ImportJob
from ulabel.domain.ports.import_job_repository import ImportJobRepository


class InMemoryImportJobRepository(ImportJobRepository):
    """In-memory import job repository backed by a dictionary."""

    def __init__(self) -> None:
        """Initialize an empty repository."""
        self._jobs: dict[UUID, ImportJob] = {}

    async def save(self, job: ImportJob) -> None:
        self._jobs[job.id] = job

    async def get_by_id(self, job_id: UUID) -> ImportJob | None:
        return self._jobs.get(job_id)
