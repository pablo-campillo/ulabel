"""Port interface for user persistence."""

from abc import ABC, abstractmethod
from uuid import UUID

from ulabel.domain.users import User


class UserRepository(ABC):
    """Abstract repository for storing and retrieving users."""

    @abstractmethod
    async def get_by_username(self, username: str) -> User | None:
        """Retrieve a user by their username.

        Args:
            username: The exact username to search for.

        Returns:
            The user if found, None otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None:
        """Retrieve a user by their unique identifier.

        Args:
            user_id: The unique identifier of the user.

        Returns:
            The user if found, None otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_by_ids(self, user_ids: set[UUID]) -> list[User]:
        """Retrieve multiple users by their unique identifiers in a single query.

        Args:
            user_ids: The set of user IDs to look up.

        Returns:
            A list of found users. Missing IDs are silently skipped.
        """
        raise NotImplementedError

    @abstractmethod
    async def search_by_username_prefix(
        self, prefix: str, *, role: str | None = None, limit: int = 10
    ) -> list[User]:
        """Search for users whose username starts with the given prefix.

        Args:
            prefix: The username prefix to match.
            role: Optional role filter to narrow results.
            limit: Maximum number of users to return.

        Returns:
            A list of matching users.
        """
        raise NotImplementedError
