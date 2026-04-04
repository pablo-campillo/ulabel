"""Use case for retrieving the status of a bulk image import job."""

from uuid import UUID

from ulabel.domain.import_jobs import ImportJob, ImportJobNotFound
from ulabel.domain.ports.import_job_repository import ImportJobRepository


class GetImportJobUseCase:
    """Retrieves an import job by its ID for status polling.

    Raises:
        ImportJobNotFound: If the job does not exist or belongs to a different project.
    """

    def __init__(self, import_job_repository: ImportJobRepository):
        """Initialize the use case.

        Args:
            import_job_repository: Repository for import job lookups.
        """
        self._import_job_repository = import_job_repository

    async def execute(self, import_id: UUID, project_id: UUID) -> ImportJob:
        """Retrieve an import job by its ID.

        Args:
            import_id: The unique ID of the import job.
            project_id: The project ID to verify ownership.

        Returns:
            The matching import job.

        Raises:
            ImportJobNotFound: If the job does not exist or belongs to a different project.
        """
        job = await self._import_job_repository.get_by_id(import_id)
        if job is None or job.project_id != project_id:
            raise ImportJobNotFound("Import job not found")
        return job
