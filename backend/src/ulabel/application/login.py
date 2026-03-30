"""Use case for authenticating a user by username."""

from ulabel.domain.errors import DomainError
from ulabel.domain.ports.user_repository import UserRepository
from ulabel.domain.users import User


class UserNotFound(DomainError):
    """Raised when a user with the given identifier does not exist."""

    pass


class LoginUseCase:
    """Authenticates a user by looking up their username.

    Returns the user entity if found, otherwise raises an error.
    """

    def __init__(self, user_repository: UserRepository):
        """Initialize the use case.

        Args:
            user_repository: Repository for user lookups.
        """
        self.user_repository = user_repository

    async def execute(self, username: str) -> User:
        """Log in a user by username.

        Args:
            username: The username to authenticate.

        Returns:
            The authenticated user entity.

        Raises:
            UserNotFound: If no user with the given username exists.
        """
        user = await self.user_repository.get_by_username(username)
        if user is None:
            raise UserNotFound("User not found")
        return user
