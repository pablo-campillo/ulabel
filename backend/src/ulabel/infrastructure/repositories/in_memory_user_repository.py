from uuid import UUID

from ulabel.domain.ports.user_repository import UserRepository
from ulabel.domain.users import User


class InMemoryUserRepository(UserRepository):

    def __init__(self, users: list[User] | None = None):
        self._by_username: dict[str, User] = {u.username: u for u in (users or [])}
        self._by_id: dict[UUID, User] = {u.id: u for u in (users or [])}

    async def get_by_username(self, username: str) -> User | None:
        return self._by_username.get(username)

    async def get_by_id(self, user_id: UUID) -> User | None:
        return self._by_id.get(user_id)
