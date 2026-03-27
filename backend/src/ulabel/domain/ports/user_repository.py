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
