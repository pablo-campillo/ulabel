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
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


@dataclass
class ImportJob:
    id: UUID
    project_id: UUID
    prefix: str
    status: ImportJobStatus
    imported: int = field(default=0)
    error: str | None = field(default=None)


class ImportJobNotFound(DomainError):
    pass


class ImportImagesFromStorageUseCase:

    def __init__(
        self,
        project_repository: ProjectRepository,
        image_repository: ImageRepository,
        storage_service: StorageService,
    ):
        self._project_repository = project_repository
        self._image_repository = image_repository
        self._storage_service = storage_service

    async def start(self, project_id: UUID, prefix: str) -> ImportJob:
        project = await self._project_repository.get_by_id(project_id)
        if project is None:
            raise ProjectNotFound("Project not found")

        job = ImportJob(id=uuid4(), project_id=project_id, prefix=prefix, status=ImportJobStatus.RUNNING)
        _jobs[job.id] = job
        return job

    async def run(self, job: ImportJob) -> None:
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
        job = _jobs.get(import_id)
        if job is None or job.project_id != project_id:
            raise ImportJobNotFound("Import job not found")
        return job
