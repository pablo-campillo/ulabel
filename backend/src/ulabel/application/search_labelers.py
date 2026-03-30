"""Use case for searching labeler users by username prefix."""

from dataclasses import dataclass

from ulabel.domain.ports.user_repository import UserRepository
from ulabel.domain.users import User, UserRole


@dataclass
class SearchLabelersUseCase:
    """Searches for users with the labeler role by username prefix.

    Useful for autocomplete when assigning labelers to projects.
    """

    user_repository: UserRepository

    async def execute(self, prefix: str, limit: int = 10) -> list[User]:
        """Search for labelers whose username starts with the given prefix.

        Args:
            prefix: The username prefix to search for.
            limit: Maximum number of results to return.

        Returns:
            A list of matching labeler users.
        """
        return await self.user_repository.search_by_username_prefix(
            prefix, role=UserRole.LABELER, limit=limit
        )
