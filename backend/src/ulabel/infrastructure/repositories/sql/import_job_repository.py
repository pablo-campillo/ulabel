"""SQLAlchemy implementation of the import job repository.

Provides PostgreSQL-backed persistence for import jobs using upsert semantics.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from ulabel.domain.import_jobs import ImportJob
from ulabel.domain.ports.import_job_repository import ImportJobRepository
from ulabel.infrastructure.models.import_job import ImportJobModel


class SqlAlchemyImportJobRepository(ImportJobRepository):
    """PostgreSQL-backed import job repository using SQLAlchemy."""

    def __init__(self, session: AsyncSession):
        """Initialize with a shared async session.

        Args:
            session: The async database session managed by the Unit of Work.
        """
        self._session = session

    async def save(self, job: ImportJob) -> None:
        """Save or update an import job using upsert semantics.

        Args:
            job: The domain ImportJob to persist.
        """
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
        await self._session.execute(stmt)

    async def get_by_id(self, job_id: UUID) -> ImportJob | None:
        """Retrieve an import job by its ID.

        Args:
            job_id: The import job's unique identifier.

        Returns:
            The domain ImportJob if found, otherwise None.
        """
        result = await self._session.execute(
            select(ImportJobModel).where(ImportJobModel.id == job_id)
        )
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None
