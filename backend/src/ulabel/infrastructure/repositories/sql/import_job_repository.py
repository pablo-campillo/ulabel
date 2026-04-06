"""SQLAlchemy implementation of the import job repository.

Provides PostgreSQL-backed persistence for import jobs using upsert semantics.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ulabel.domain.import_jobs import ImportJob
from ulabel.domain.ports.import_job_repository import ImportJobRepository
from ulabel.infrastructure.models.import_job import ImportJobModel


class SqlAlchemyImportJobRepository(ImportJobRepository):
    """PostgreSQL-backed import job repository using SQLAlchemy."""

    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]):
        """Initialize with an async session factory.

        Args:
            sessionmaker: Factory for creating async database sessions.
        """
        self._sessionmaker = sessionmaker

    async def save(self, job: ImportJob) -> None:
        """Save or update an import job using upsert semantics.

        Args:
            job: The domain ImportJob to persist.
        """
        async with self._sessionmaker() as session:
            stmt = (
                insert(ImportJobModel)
                .values(
                    id=job.id,
                    project_id=job.project_id,
                    prefix=job.prefix,
                    status=job.status.value,
                    imported=job.imported,
                    error=job.error,
                )
                .on_conflict_do_update(
                    index_elements=["id"],
                    set_={
                        "status": job.status.value,
                        "imported": job.imported,
                        "error": job.error,
                    },
                )
            )
            await session.execute(stmt)
            await session.commit()

    async def get_by_id(self, job_id: UUID) -> ImportJob | None:
        """Retrieve an import job by its ID.

        Args:
            job_id: The import job's unique identifier.

        Returns:
            The domain ImportJob if found, otherwise None.
        """
        async with self._sessionmaker() as session:
            result = await session.execute(
                select(ImportJobModel).where(ImportJobModel.id == job_id)
            )
            model = result.scalar_one_or_none()
            return model.to_domain() if model else None
