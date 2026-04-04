"""Use case for bulk-importing images from object storage into a project."""

from uuid import UUID, uuid4

from ulabel.application.add_labeler_to_project import ProjectNotFound
from ulabel.domain.images import Image
from ulabel.domain.import_jobs import ImportJob
from ulabel.domain.ports.image_repository import ImageRepository
from ulabel.domain.ports.import_job_repository import ImportJobRepository
from ulabel.domain.ports.project_repository import ProjectRepository
from ulabel.domain.ports.storage_service import StorageService

_CHUNK_SIZE = 1000


class ImportImagesFromStorageUseCase:
    """Imports images from an object storage prefix into a project in chunks.

    Creates an import job that can be polled for progress while the
    actual import runs asynchronously in the background.
    """

    def __init__(
        self,
        project_repository: ProjectRepository,
        image_repository: ImageRepository,
        storage_service: StorageService,
        import_job_repository: ImportJobRepository,
    ):
        """Initialize the use case.

        Args:
            project_repository: Repository for project lookups.
            image_repository: Repository for bulk image persistence.
            storage_service: Service for listing objects in storage.
            import_job_repository: Repository for import job persistence.
        """
        self._project_repository = project_repository
        self._image_repository = image_repository
        self._storage_service = storage_service
        self._import_job_repository = import_job_repository

    async def execute(self, project_id: UUID, prefix: str) -> ImportJob:
        """Start a new import job for a project.

        Validates the project exists, creates and persists the import job,
        and returns it immediately. The caller is responsible for scheduling
        ``run_import`` as a background task.

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

        job = ImportJob.create(id=uuid4(), project_id=project_id, prefix=prefix)
        await self._import_job_repository.save(job)
        return job

    async def run_import(self, job_id: UUID) -> None:
        """Execute the import, saving images in chunks and updating job progress.

        Loads the job from the repository, iterates over storage objects,
        and persists images in batches. Updates the job status in the
        repository after each chunk and on completion or failure.

        Args:
            job_id: The ID of the import job to execute.
        """
        job = await self._import_job_repository.get_by_id(job_id)
        if job is None:
            return

        try:
            chunk: list[Image] = []
            async for storage_key in self._storage_service.list_objects(job.prefix):
                chunk.append(Image.create(id=uuid4(), project_id=job.project_id, storage_key=storage_key))
                if len(chunk) >= _CHUNK_SIZE:
                    await self._image_repository.save_bulk(chunk)
                    job.mark_progress(len(chunk))
                    await self._import_job_repository.save(job)
                    chunk = []
            if chunk:
                await self._image_repository.save_bulk(chunk)
                job.mark_progress(len(chunk))
            job.mark_done()
        except Exception as e:
            job.mark_failed(str(e))

        await self._import_job_repository.save(job)
