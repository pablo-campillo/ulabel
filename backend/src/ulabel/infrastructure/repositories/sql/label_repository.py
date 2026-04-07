"""SQLAlchemy implementation of the label repository.

Provides PostgreSQL-backed persistence for label records, including
saving, counting, and exporting label data.
"""

from collections.abc import AsyncIterator
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from ulabel.domain.labels import LabelExportRow, LabelRecord
from ulabel.domain.ports.label_repository import LabelRepository
from ulabel.infrastructure.models.image import ImageModel
from ulabel.infrastructure.models.label import LabelRecordModel


class SqlAlchemyLabelRepository(LabelRepository):
    """PostgreSQL-backed label repository using SQLAlchemy."""

    def __init__(self, session: AsyncSession):
        """Initialize with a shared async session.

        Args:
            session: The async database session managed by the Unit of Work.
        """
        self._session = session

    async def save(self, label_record: LabelRecord) -> None:
        """Persist a label record, ignoring conflicts on duplicate image IDs.

        Args:
            label_record: The domain LabelRecord to save.
        """
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
        await self._session.execute(stmt)

    async def count_by_project(self, project_id: UUID) -> int:
        """Count the total number of labels for a project.

        Args:
            project_id: The project to count labels for.

        Returns:
            The total label count.
        """
        result = await self._session.execute(
            select(func.count(LabelRecordModel.id)).where(LabelRecordModel.project_id == project_id)
        )
        return result.scalar_one()

    async def get_export_data(self, project_id: UUID) -> AsyncIterator[LabelExportRow]:
        """Retrieve label data joined with image storage keys for export as a stream.

        Args:
            project_id: The project to export labels for.

        Yields:
            LabelExportRow objects ordered by image ID.
        """
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
        result = await self._session.stream(stmt)
        async for row in result:
            yield LabelExportRow(
                image_id=row.image_id,
                storage_key=row.storage_key,
                value=row.label,
            )
