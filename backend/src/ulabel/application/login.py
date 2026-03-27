from ulabel.domain.ports.user_repository import UserRepository
from ulabel.domain.users import User


class UserNotFound(Exception):
    pass


class LoginUseCase:

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, username: str) -> User:
        user = await self.user_repository.get_by_username(username)
        if user is None:
            raise UserNotFound(f"User '{username}' not found")
        return user
