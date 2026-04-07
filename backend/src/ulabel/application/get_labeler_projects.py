"""Use case for retrieving all projects assigned to a labeler."""

from uuid import UUID

from ulabel.application.create_project import Unauthorized
from ulabel.application.login import UserNotFound
from ulabel.domain.ports.unit_of_work import UnitOfWork
from ulabel.domain.projects import Project
from ulabel.domain.users import UserRole


class GetLabelerProjectsUseCase:
    """Retrieves the list of projects a labeler is assigned to.

    Validates that the user exists and holds the labeler role.
    """

    def __init__(self, uow: UnitOfWork):
        """Initialize the use case.

        Args:
            uow: Unit of Work for transactional repository access.
        """
        self._uow = uow

    async def execute(self, labeler_id: UUID) -> list[Project]:
        """Get all projects for a labeler.

        Args:
            labeler_id: The ID of the labeler user.

        Returns:
            A list of projects the labeler is assigned to.

        Raises:
            UserNotFound: If the labeler user does not exist.
            Unauthorized: If the user does not have the labeler role.
        """
        async with self._uow as uow:
            labeler = await uow.user_repository.get_by_id(labeler_id)
            if labeler is None:
                raise UserNotFound("Labeler not found")
            if labeler.role != UserRole.LABELER:
                raise Unauthorized("User is not a labeler")
            return await uow.project_repository.get_by_labeler_id(labeler_id)
