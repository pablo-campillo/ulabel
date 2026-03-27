from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ulabel.domain.ports.user_repository import UserRepository
from ulabel.domain.users import User
from ulabel.infrastructure.models.user import UserModel


class SqlAlchemyUserRepository(UserRepository):

    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]):
        self._sessionmaker = sessionmaker

    async def get_by_username(self, username: str) -> User | None:
        async with self._sessionmaker() as session:
            result = await session.execute(
                select(UserModel).where(UserModel.username == username)
            )
            model = result.scalar_one_or_none()
            return model.to_domain() if model else None

    async def get_by_id(self, user_id: UUID) -> User | None:
        async with self._sessionmaker() as session:
            result = await session.execute(
                select(UserModel).where(UserModel.id == user_id)
            )
            model = result.scalar_one_or_none()
            return model.to_domain() if model else None

    async def search_by_username_prefix(
        self, prefix: str, *, role: str | None = None, limit: int = 10
    ) -> list[User]:
        async with self._sessionmaker() as session:
            stmt = select(UserModel).where(UserModel.username.ilike(f"{prefix}%"))
            if role is not None:
                stmt = stmt.where(UserModel.role == role)
            stmt = stmt.order_by(UserModel.username).limit(limit)
            result = await session.execute(stmt)
            return [row.to_domain() for row in result.scalars()]

    async def save(self, user: User) -> None:
        async with self._sessionmaker() as session:
            stmt = (
                insert(UserModel)
                .values(id=user.id, username=user.username, role=user.role.value)
                .on_conflict_do_update(
                    index_elements=["id"],
                    set_={"username": user.username, "role": user.role.value},
                )
            )
            await session.execute(stmt)
            await session.commit()
