from uuid import UUID, uuid4

from ulabel.application.add_labeler_to_project import ProjectNotFound
from ulabel.domain.images import Image
from ulabel.domain.ports.image_repository import ImageRepository
from ulabel.domain.ports.project_repository import ProjectRepository
from ulabel.domain.ports.storage_service import StorageService


class UploadImageToProjectUseCase:

    def __init__(
        self,
        project_repository: ProjectRepository,
        image_repository: ImageRepository,
        storage_service: StorageService,
    ):
        self.project_repository = project_repository
        self.image_repository = image_repository
        self.storage_service = storage_service

    async def execute(self, project_id: UUID, data: bytes, content_type: str) -> Image:
        project = await self.project_repository.get_by_id(project_id)
        if project is None:
            raise ProjectNotFound(f"Project '{project_id}' not found")

        image_id = uuid4()
        storage_key = f"{project_id}/{image_id}"
        await self.storage_service.upload_file(key=storage_key, data=data, content_type=content_type, size=len(data))
        image = Image.create(id=image_id, project_id=project_id, storage_key=storage_key)
        await self.image_repository.save(image)
        return image
