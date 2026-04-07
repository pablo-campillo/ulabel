"""Use case for searching labeler users by username prefix."""

from ulabel.domain.ports.unit_of_work import UnitOfWork
from ulabel.domain.users import User, UserRole


class SearchLabelersUseCase:
    """Searches for users with the labeler role by username prefix.

    Useful for autocomplete when assigning labelers to projects.
    """

    def __init__(self, uow: UnitOfWork):
        """Initialize the use case.

        Args:
            uow: Unit of Work for transactional repository access.
        """
        self._uow = uow

    async def execute(self, prefix: str, limit: int = 10) -> list[User]:
        """Search for labelers whose username starts with the given prefix.

        Args:
            prefix: The username prefix to search for.
            limit: Maximum number of results to return.

        Returns:
            A list of matching labeler users.
        """
        async with self._uow as uow:
            return await uow.user_repository.search_by_username_prefix(
                prefix, role=UserRole.LABELER, limit=limit
            )
