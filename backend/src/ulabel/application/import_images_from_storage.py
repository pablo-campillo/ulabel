"""Use case for bulk-importing images from object storage into a project."""

from dataclasses import dataclass, field
from enum import StrEnum
from uuid import UUID, uuid4

from ulabel.application.add_labeler_to_project import ProjectNotFound
from ulabel.domain.errors import DomainError
from ulabel.domain.images import Image
from ulabel.domain.ports.image_repository import ImageRepository
from ulabel.domain.ports.project_repository import ProjectRepository
from ulabel.domain.ports.storage_service import StorageService

_CHUNK_SIZE = 1000
_jobs: dict[UUID, "ImportJob"] = {}


class ImportJobStatus(StrEnum):
    """Status of a bulk image import job."""

    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


@dataclass
class ImportJob:
    """Tracks the state and progress of a bulk image import operation."""

    id: UUID
    project_id: UUID
    prefix: str
    status: ImportJobStatus
    imported: int = field(default=0)
    error: str | None = field(default=None)


class ImportJobNotFound(DomainError):
    """Raised when a referenced import job does not exist."""

    pass


class ImportImagesFromStorageUseCase:
    """Imports images from an object storage prefix into a project in chunks.

    Creates an import job that can be started and then run asynchronously,
    with progress tracked via the job object.
    """

    def __init__(
        self,
        project_repository: ProjectRepository,
        image_repository: ImageRepository,
        storage_service: StorageService,
    ):
        """Initialize the use case.

        Args:
            project_repository: Repository for project lookups.
            image_repository: Repository for bulk image persistence.
            storage_service: Service for listing objects in storage.
        """
        self._project_repository = project_repository
        self._image_repository = image_repository
        self._storage_service = storage_service

    async def start(self, project_id: UUID, prefix: str) -> ImportJob:
        """Start a new import job for a project.

        Args:
            project_id: The project to import images into.
            prefix: The object storage prefix to list images from.

        Returns:
            The newly created import job in running status.

        Raises:
            ProjectNotFound: If the project does not exist.
        """
        project = await self._project_repository.get_by_id(project_id)
        if project is None:
            raise ProjectNotFound("Project not found")

        job = ImportJob(id=uuid4(), project_id=project_id, prefix=prefix, status=ImportJobStatus.RUNNING)
        _jobs[job.id] = job
        return job

    async def run(self, job: ImportJob) -> None:
        """Execute the import, saving images in chunks and updating job progress.

        Args:
            job: The import job to execute. Its status and counters are
                updated in place as the import progresses.
        """
        try:
            chunk: list[Image] = []
            async for storage_key in self._storage_service.list_objects(job.prefix):
                chunk.append(Image.create(id=uuid4(), project_id=job.project_id, storage_key=storage_key))
                if len(chunk) >= _CHUNK_SIZE:
                    await self._image_repository.save_bulk(chunk)
                    job.imported += len(chunk)
                    chunk = []
            if chunk:
                await self._image_repository.save_bulk(chunk)
                job.imported += len(chunk)
            job.status = ImportJobStatus.DONE
        except Exception as e:
            job.status = ImportJobStatus.FAILED
            job.error = str(e)

    @staticmethod
    def get_job(import_id: UUID, project_id: UUID) -> ImportJob:
        """Retrieve an import job by its ID.

        Args:
            import_id: The unique ID of the import job.
            project_id: The project ID to verify ownership.

        Returns:
            The matching import job.

        Raises:
            ImportJobNotFound: If the job does not exist or belongs to a different project.
        """
        job = _jobs.get(import_id)
        if job is None or job.project_id != project_id:
            raise ImportJobNotFound("Import job not found")
        return job
