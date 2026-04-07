"""SQLAlchemy implementation of the statistics repository.

Provides PostgreSQL-backed queries for image counts, labeler rankings,
class distributions, and daily activity breakdowns.
"""

from uuid import UUID

from sqlalchemy import Date, case, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ulabel.domain.labels import LabelerSubmitStats
from ulabel.domain.ports.stats_repository import (
    DailyLabelRow,
    ImageCounts,
    LabelerClassRow,
    StatsRepository,
)
from ulabel.infrastructure.models.image import ImageModel
from ulabel.infrastructure.models.label import LabelRecordModel
from ulabel.infrastructure.models.user import UserModel


class SqlAlchemyStatsRepository(StatsRepository):
    """PostgreSQL-backed statistics repository using SQLAlchemy."""

    def __init__(self, session: AsyncSession):
        """Initialize with a shared async session.

        Args:
            session: The async database session managed by the Unit of Work.
        """
        self._session = session

    async def get_image_counts(self, project_id: UUID) -> ImageCounts:
        """Get total and labeled image counts for a project.

        Args:
            project_id: The project to count images for.

        Returns:
            An ImageCounts with total and labeled counts.
        """
        stmt = select(
            func.count().label("total"),
            func.count(case((ImageModel.status == "done", 1))).label("labeled"),
        ).where(ImageModel.project_id == project_id)
        row = (await self._session.execute(stmt)).one()
        return ImageCounts(total=row.total, labeled=row.labeled)

    async def get_labeler_class_counts(self, project_id: UUID) -> list[LabelerClassRow]:
        """Get per-labeler, per-class label counts for a project.

        Args:
            project_id: The project to query.

        Returns:
            A list of LabelerClassRow with labeler, class, and count data.
        """
        stmt = (
            select(
                LabelRecordModel.labeler_id,
                UserModel.username,
                LabelRecordModel.label,
                func.count().label("cnt"),
            )
            .join(UserModel, LabelRecordModel.labeler_id == UserModel.id)
            .where(LabelRecordModel.project_id == project_id)
            .group_by(
                LabelRecordModel.labeler_id,
                UserModel.username,
                LabelRecordModel.label,
            )
        )
        rows = (await self._session.execute(stmt)).all()
        return [
            LabelerClassRow(
                labeler_id=r.labeler_id,
                username=r.username,
                label=r.label,
                count=r.cnt,
            )
            for r in rows
        ]

    async def get_daily_label_counts(self, project_id: UUID) -> list[DailyLabelRow]:
        """Get daily per-labeler, per-class label counts for a project.

        Args:
            project_id: The project to query.

        Returns:
            A list of DailyLabelRow ordered by date.
        """
        day_col = cast(LabelRecordModel.created_at, Date).label("day")
        stmt = (
            select(
                LabelRecordModel.labeler_id,
                UserModel.username,
                day_col,
                LabelRecordModel.label,
                func.count().label("cnt"),
            )
            .join(UserModel, LabelRecordModel.labeler_id == UserModel.id)
            .where(LabelRecordModel.project_id == project_id)
            .group_by(
                LabelRecordModel.labeler_id,
                UserModel.username,
                day_col,
                LabelRecordModel.label,
            )
            .order_by(day_col)
        )
        rows = (await self._session.execute(stmt)).all()
        return [
            DailyLabelRow(
                labeler_id=r.labeler_id,
                username=r.username,
                day=r.day,
                label=r.label,
                count=r.cnt,
            )
            for r in rows
        ]

    async def get_labeler_ranking(self, project_id: UUID, labeler_id: UUID) -> LabelerSubmitStats:
        """Compute a labeler's ranking within a project.

        Args:
            project_id: The project to compute rankings for.
            labeler_id: The labeler whose ranking to determine.

        Returns:
            A LabelerSubmitStats with count, ranking position, and total labelers.
        """
        # Subquery: count per labeler in this project
        counts_sq = (
            select(
                LabelRecordModel.labeler_id,
                func.count().label("cnt"),
            )
            .where(LabelRecordModel.project_id == project_id)
            .group_by(LabelRecordModel.labeler_id)
            .subquery()
        )

        # Get total labelers who have submitted at least one label
        total_stmt = select(func.count()).select_from(counts_sq)
        total_labelers = (await self._session.execute(total_stmt)).scalar_one()

        # Get this labeler's count
        labeler_cnt_stmt = select(counts_sq.c.cnt).where(counts_sq.c.labeler_id == labeler_id)
        labeler_count = (await self._session.execute(labeler_cnt_stmt)).scalar_one_or_none() or 0

        # Ranking: how many labelers have strictly more labels than this one
        ranking_stmt = (
            select(func.count()).select_from(counts_sq).where(counts_sq.c.cnt > labeler_count)
        )
        above = (await self._session.execute(ranking_stmt)).scalar_one()
        ranking = above + 1

        return LabelerSubmitStats(
            labeler_count=labeler_count,
            ranking=ranking,
            total_labelers=total_labelers,
        )
