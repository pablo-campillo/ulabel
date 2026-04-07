"""Use case for authenticating a user by username."""

from ulabel.domain.errors import DomainError
from ulabel.domain.ports.unit_of_work import UnitOfWork
from ulabel.domain.users import User


class UserNotFound(DomainError):
    """Raised when a user with the given identifier does not exist."""

    pass


class LoginUseCase:
    """Authenticates a user by looking up their username.

    Returns the user entity if found, otherwise raises an error.
    """

    def __init__(self, uow: UnitOfWork):
        """Initialize the use case.

        Args:
            uow: Unit of Work for transactional repository access.
        """
        self._uow = uow

    async def execute(self, username: str) -> User:
        """Log in a user by username.

        Args:
            username: The username to authenticate.

        Returns:
            The authenticated user entity.

        Raises:
            UserNotFound: If no user with the given username exists.
        """
        async with self._uow as uow:
            user = await uow.user_repository.get_by_username(username)
            if user is None:
                raise UserNotFound("User not found")
            return user
