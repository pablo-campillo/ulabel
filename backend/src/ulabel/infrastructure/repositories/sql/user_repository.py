"""SQLAlchemy implementation of the user repository.

Provides PostgreSQL-backed persistence for users with lookup by
username, ID, prefix search, and upsert support.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from ulabel.domain.ports.user_repository import UserRepository
from ulabel.domain.users import User
from ulabel.infrastructure.models.user import UserModel


class SqlAlchemyUserRepository(UserRepository):
    """PostgreSQL-backed user repository using SQLAlchemy."""

    def __init__(self, session: AsyncSession):
        """Initialize with a shared async session.

        Args:
            session: The async database session managed by the Unit of Work.
        """
        self._session = session

    async def get_by_username(self, username: str) -> User | None:
        """Retrieve a user by their unique username.

        Args:
            username: The username to look up.

        Returns:
            The domain User if found, otherwise None.
        """
        result = await self._session.execute(
            select(UserModel).where(UserModel.username == username)
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Retrieve a user by their unique ID.

        Args:
            user_id: The user's unique identifier.

        Returns:
            The domain User if found, otherwise None.
        """
        result = await self._session.execute(select(UserModel).where(UserModel.id == user_id))
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_by_ids(self, user_ids: set[UUID]) -> list[User]:
        """Retrieve multiple users by ID in a single query.

        Args:
            user_ids: The set of user IDs to look up.

        Returns:
            A list of found domain Users.
        """
        if not user_ids:
            return []
        result = await self._session.execute(select(UserModel).where(UserModel.id.in_(user_ids)))
        return [row.to_domain() for row in result.scalars()]

    async def search_by_username_prefix(
        self, prefix: str, *, role: str | None = None, limit: int = 10
    ) -> list[User]:
        """Search users by username prefix with optional role filter.

        Args:
            prefix: The username prefix to match (case-insensitive).
            role: Optional role to filter by.
            limit: Maximum number of results.

        Returns:
            A list of matching Users ordered by username.
        """
        stmt = select(UserModel).where(UserModel.username.ilike(f"{prefix}%"))
        if role is not None:
            stmt = stmt.where(UserModel.role == role)
        stmt = stmt.order_by(UserModel.username).limit(limit)
        result = await self._session.execute(stmt)
        return [row.to_domain() for row in result.scalars()]

    async def save(self, user: User) -> None:
        """Save or update a user using upsert semantics.

        Args:
            user: The domain User to persist.
        """
        stmt = (
            insert(UserModel)
            .values(id=user.id, username=user.username, role=user.role.value)
            .on_conflict_do_update(
                index_elements=["id"],
                set_={"username": user.username, "role": user.role.value},
            )
        )
        await self._session.execute(stmt)
