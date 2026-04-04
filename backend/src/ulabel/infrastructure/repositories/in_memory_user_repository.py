"""In-memory implementation of the user repository for testing."""

from uuid import UUID

from ulabel.domain.ports.user_repository import UserRepository
from ulabel.domain.users import User


class InMemoryUserRepository(UserRepository):
    """In-memory user repository backed by username and ID dictionaries."""

    def __init__(self, users: list[User] | None = None):
        """Initialize with optional seed users.

        Args:
            users: Optional list of users to pre-populate the repository.
        """
        self._by_username: dict[str, User] = {u.username: u for u in (users or [])}
        self._by_id: dict[UUID, User] = {u.id: u for u in (users or [])}

    async def get_by_username(self, username: str) -> User | None:
        return self._by_username.get(username)

    async def get_by_id(self, user_id: UUID) -> User | None:
        return self._by_id.get(user_id)

    async def get_by_ids(self, user_ids: set[UUID]) -> list[User]:
        return [self._by_id[uid] for uid in user_ids if uid in self._by_id]

    async def search_by_username_prefix(
        self, prefix: str, *, role: str | None = None, limit: int = 10
    ) -> list[User]:
        prefix_lower = prefix.lower()
        results = [
            u
            for u in self._by_username.values()
            if u.username.lower().startswith(prefix_lower)
            and (role is None or u.role == role)
        ]
        results.sort(key=lambda u: u.username)
        return results[:limit]
