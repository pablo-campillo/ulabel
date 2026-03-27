from uuid import UUID, uuid4

from ulabel.application.add_labeler_to_project import ProjectNotFound
from ulabel.domain.images import Image
from ulabel.domain.ports.image_repository import ImageRepository
from ulabel.domain.ports.project_repository import ProjectRepository


class AddImageToProjectUseCase:

    def __init__(self, project_repository: ProjectRepository, image_repository: ImageRepository):
        self.project_repository = project_repository
        self.image_repository = image_repository

    async def execute(self, project_id: UUID, storage_key: str) -> Image:
        project = await self.project_repository.get_by_id(project_id)
        if project is None:
            raise ProjectNotFound(f"Project '{project_id}' not found")

        image = Image.create(id=uuid4(), project_id=project_id, storage_key=storage_key)
        await self.image_repository.save(image)
        return image
