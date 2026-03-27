from dataclasses import dataclass

from ulabel.domain.ports.user_repository import UserRepository
from ulabel.domain.users import User, UserRole


@dataclass
class SearchLabelersUseCase:
    user_repository: UserRepository

    async def execute(self, prefix: str, limit: int = 10) -> list[User]:
        return await self.user_repository.search_by_username_prefix(
            prefix, role=UserRole.LABELER, limit=limit
        )
