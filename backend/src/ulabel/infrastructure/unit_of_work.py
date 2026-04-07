"""SQLAlchemy implementation of the Unit of Work pattern.

Opens a single database session shared by all repositories for the
duration of one logical operation, ensuring atomicity and reducing
connection overhead.
"""

from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ulabel.domain.ports.unit_of_work import UnitOfWork
from ulabel.infrastructure.repositories.sql.image_repository import SqlAlchemyImageRepository
from ulabel.infrastructure.repositories.sql.import_job_repository import (
    SqlAlchemyImportJobRepository,
)
from ulabel.infrastructure.repositories.sql.label_repository import SqlAlchemyLabelRepository
from ulabel.infrastructure.repositories.sql.project_repository import (
    SqlAlchemyProjectRepository,
)
from ulabel.infrastructure.repositories.sql.stats_repository import SqlAlchemyStatsRepository
from ulabel.infrastructure.repositories.sql.user_repository import SqlAlchemyUserRepository


class SqlAlchemyUnitOfWork(UnitOfWork):
    """SQLAlchemy-backed Unit of Work.

    Creates a single ``AsyncSession`` on entry and constructs all
    repositories sharing that session. Supports being entered multiple
    times (each entry creates a fresh session).
    """

    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]):
        self._sessionmaker = sessionmaker

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        self._session: AsyncSession = self._sessionmaker()
        await self._session.__aenter__()

        self.project_repository = SqlAlchemyProjectRepository(self._session)
        self.image_repository = SqlAlchemyImageRepository(self._session)
        self.label_repository = SqlAlchemyLabelRepository(self._session)
        self.stats_repository = SqlAlchemyStatsRepository(self._session)
        self.user_repository = SqlAlchemyUserRepository(self._session)
        self.import_job_repository = SqlAlchemyImportJobRepository(self._session)

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            await self.rollback()
        await self._session.__aexit__(exc_type, exc_val, exc_tb)

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
