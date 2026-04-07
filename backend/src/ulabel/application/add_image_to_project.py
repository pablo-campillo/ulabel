"""Use case for adding an image reference to a labeling project."""

from uuid import UUID, uuid4

from ulabel.application.add_labeler_to_project import ProjectNotFound
from ulabel.domain.images import Image
from ulabel.domain.ports.unit_of_work import UnitOfWork


class AddImageToProjectUseCase:
    """Registers an already-uploaded image in a project by its storage key.

    Validates that the target project exists before persisting the image.
    """

    def __init__(self, uow: UnitOfWork):
        """Initialize the use case.

        Args:
            uow: Unit of Work for transactional repository access.
        """
        self._uow = uow

    async def execute(self, project_id: UUID, storage_key: str) -> Image:
        """Add an image to a project.

        Args:
            project_id: The ID of the target project.
            storage_key: The object storage key where the image data resides.

        Returns:
            The newly created image entity.

        Raises:
            ProjectNotFound: If the project does not exist.
        """
        async with self._uow as uow:
            project = await uow.project_repository.get_by_id(project_id)
            if project is None:
                raise ProjectNotFound(f"Project '{project_id}' not found")

            image = Image.create(id=uuid4(), project_id=project_id, storage_key=storage_key)
            await uow.image_repository.save(image)
            await uow.commit()
            return image
