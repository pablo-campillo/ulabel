"""SQLAlchemy ORM model for import jobs.

Maps the ``import_jobs`` table and provides conversion between the
database representation and the domain ImportJob entity.
"""

from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from ulabel.domain.import_jobs import ImportJob, ImportJobStatus
from ulabel.infrastructure.models.base import Base


class ImportJobModel(Base):
    """ORM model representing a bulk image import job."""

    __tablename__ = "import_jobs"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True
    )
    prefix: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    imported: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    def to_domain(self) -> ImportJob:
        """Convert this ORM model to a domain ImportJob entity.

        Returns:
            The corresponding domain ImportJob.
        """
        return ImportJob(
            id=self.id,
            project_id=self.project_id,
            prefix=self.prefix,
            status=ImportJobStatus(self.status),
            imported=self.imported,
            error=self.error,
        )

    @classmethod
    def from_domain(cls, job: ImportJob) -> "ImportJobModel":
        """Create an ORM model from a domain ImportJob entity.

        Args:
            job: The domain ImportJob to convert.

        Returns:
            A new ImportJobModel instance.
        """
        return cls(
            id=job.id,
            project_id=job.project_id,
            prefix=job.prefix,
            status=job.status.value,
            imported=job.imported,
            error=job.error,
        )
