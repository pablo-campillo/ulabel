from abc import ABC, abstractmethod
from uuid import UUID

from ulabel.domain.users import User


class UserRepository(ABC):

    @abstractmethod
    async def get_by_username(self, username: str) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def search_by_username_prefix(
        self, prefix: str, *, role: str | None = None, limit: int = 10
    ) -> list[User]:
        raise NotImplementedError
