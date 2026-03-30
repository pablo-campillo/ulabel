"""SQLAlchemy implementation of the label repository.

Provides PostgreSQL-backed persistence for label records, including
saving, counting, and exporting label data.
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ulabel.domain.labels import LabelExportRow, LabelRecord
from ulabel.domain.ports.label_repository import LabelRepository
from ulabel.infrastructure.models.image import ImageModel
from ulabel.infrastructure.models.label import LabelRecordModel


class SqlAlchemyLabelRepository(LabelRepository):
    """PostgreSQL-backed label repository using SQLAlchemy."""

    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]):
        """Initialize with an async session factory.

        Args:
            sessionmaker: Factory for creating async database sessions.
        """
        self._sessionmaker = sessionmaker

    async def save(self, label_record: LabelRecord) -> None:
        """Persist a label record, ignoring conflicts on duplicate image IDs.

        Args:
            label_record: The domain LabelRecord to save.
        """
        async with self._sessionmaker() as session:
            stmt = (
                insert(LabelRecordModel)
                .values(
                    id=label_record.id,
                    project_id=label_record.project_id,
                    image_id=label_record.image_id,
                    labeler_id=label_record.labeler_id,
                    label=label_record.label,
                )
                .on_conflict_do_nothing()
            )
            await session.execute(stmt)
            await session.commit()

    async def count_by_project(self, project_id: UUID) -> int:
        """Count the total number of labels for a project.

        Args:
            project_id: The project to count labels for.

        Returns:
            The total label count.
        """
        async with self._sessionmaker() as session:
            result = await session.execute(
                select(func.count(LabelRecordModel.id)).where(
                    LabelRecordModel.project_id == project_id
                )
            )
            return result.scalar_one()

    async def get_export_data(self, project_id: UUID) -> list[LabelExportRow]:
        """Retrieve label data joined with image storage keys for export.

        Args:
            project_id: The project to export labels for.

        Returns:
            A list of LabelExportRow objects ordered by image ID.
        """
        async with self._sessionmaker() as session:
            stmt = (
                select(
                    LabelRecordModel.image_id,
                    ImageModel.storage_key,
                    LabelRecordModel.label,
                )
                .join(ImageModel, LabelRecordModel.image_id == ImageModel.id)
                .where(LabelRecordModel.project_id == project_id)
                .order_by(LabelRecordModel.image_id)
            )
            result = await session.execute(stmt)
            return [
                LabelExportRow(image_id=row.image_id, storage_key=row.storage_key, value=row.label)
                for row in result.all()
            ]
