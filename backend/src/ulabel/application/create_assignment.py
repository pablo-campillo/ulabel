"""Use case for creating an image labeling assignment for a labeler."""

from datetime import datetime, timezone
from typing import Callable
from uuid import UUID

from ulabel.application.add_labeler_to_project import ProjectNotFound
from ulabel.domain.errors import DomainError
from ulabel.domain.images import Image
from ulabel.domain.ports.unit_of_work import UnitOfWork


class LabelerNotInProject(DomainError):
    """Raised when a labeler is not a member of the target project."""

    pass


class NoImageAvailable(DomainError):
    """Raised when no pending images are available for assignment."""

    pass


class CreateAssignmentUseCase:
    """Assigns the next pending image in a project to a labeler.

    Validates project membership and image availability before
    creating the assignment.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ):
        """Initialize the use case.

        Args:
            uow: Unit of Work for transactional repository access.
            now: Callable returning the current UTC datetime.
        """
        self._uow = uow
        self.now = now

    async def execute(self, project_id: UUID, labeler_id: UUID) -> Image:
        """Create a new assignment for the labeler.

        Args:
            project_id: The project to assign an image from.
            labeler_id: The labeler to assign the image to.

        Returns:
            The image entity with the new assignment set.

        Raises:
            ProjectNotFound: If the project does not exist.
            LabelerNotInProject: If the labeler is not a member of the project.
            NoImageAvailable: If there are no pending images to assign.
        """
        async with self._uow as uow:
            project = await uow.project_repository.get_by_id(project_id)
            if project is None:
                raise ProjectNotFound("Project not found")
            if labeler_id not in project.labeler_ids:
                raise LabelerNotInProject("Labeler is not in this project")

            image = await uow.image_repository.assign_next_pending(
                project_id=project_id,
                labeler_id=labeler_id,
                assigned_at=self.now(),
            )
            if image is None:
                raise NoImageAvailable("No pending images available")

            await uow.commit()
            return image
