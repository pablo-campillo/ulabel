from datetime import datetime, timezone
from typing import Callable
from uuid import UUID

from ulabel.application.add_labeler_to_project import ProjectNotFound
from ulabel.domain.errors import DomainError
from ulabel.domain.images import Image
from ulabel.domain.ports.image_repository import ImageRepository
from ulabel.domain.ports.project_repository import ProjectRepository


class LabelerNotInProject(DomainError):
    pass


class NoImageAvailable(DomainError):
    pass


class CreateAssignmentUseCase:

    def __init__(
        self,
        project_repository: ProjectRepository,
        image_repository: ImageRepository,
        now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ):
        self.project_repository = project_repository
        self.image_repository = image_repository
        self.now = now

    async def execute(self, project_id: UUID, labeler_id: UUID) -> Image:
        project = await self.project_repository.get_by_id(project_id)
        if project is None:
            raise ProjectNotFound("Project not found")
        if labeler_id not in project.labeler_ids:
            raise LabelerNotInProject("Labeler is not in this project")

        image = await self.image_repository.get_next_pending(project_id)
        if image is None:
            raise NoImageAvailable("No pending images available")

        image.assign(labeler_id=labeler_id, assigned_at=self.now())
        await self.image_repository.save(image)
        return image
