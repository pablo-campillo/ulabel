"""Use case for retrieving statistics and analytics for a labeling project."""

import asyncio
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from ulabel.application.add_labeler_to_project import ProjectNotFound
from ulabel.domain.ports.project_repository import ProjectRepository
from ulabel.domain.ports.stats_repository import StatsRepository


@dataclass
class LabelerClassCount:
    """Label counts per class for a single labeler."""

    labeler_id: UUID
    username: str
    counts: dict[str, int]


@dataclass
class DailyCount:
    """Label counts per class for a single day."""

    date: date
    counts: dict[str, int]


@dataclass
class LabelerDailyActivity:
    """Daily labeling activity breakdown for a single labeler."""

    labeler_id: UUID
    username: str
    daily: list[DailyCount]


@dataclass
class DailyLabelerTotal:
    """Total label count for a labeler on a given day."""

    labeler_id: UUID
    username: str
    count: int


@dataclass
class DailyTotal:
    """Aggregated labeler totals for a single day."""

    date: date
    labelers: list[DailyLabelerTotal]


@dataclass
class ProjectStats:
    """Aggregate statistics for a labeling project."""

    total_images: int
    labeled_images: int
    class_distribution: dict[str, int]
    labeler_class_counts: list[LabelerClassCount]
    labeler_daily_activity: list[LabelerDailyActivity]
    daily_totals: list[DailyTotal]


class GetProjectStatsUseCase:
    """Computes and returns comprehensive statistics for a project.

    Aggregates image counts, class distributions, per-labeler breakdowns,
    and daily activity data.
    """

    def __init__(
        self,
        project_repository: ProjectRepository,
        stats_repository: StatsRepository,
    ):
        """Initialize the use case.

        Args:
            project_repository: Repository for project lookups.
            stats_repository: Repository for statistical queries.
        """
        self._project_repository = project_repository
        self._stats_repository = stats_repository

    async def execute(self, project_id: UUID) -> ProjectStats:
        """Get statistics for a project.

        Args:
            project_id: The ID of the project to get stats for.

        Returns:
            Aggregated project statistics.

        Raises:
            ProjectNotFound: If the project does not exist.
        """
        project = await self._project_repository.get_by_id(project_id)
        if project is None:
            raise ProjectNotFound("Project not found")

        image_counts, labeler_class_rows, daily_rows = await asyncio.gather(
            self._stats_repository.get_image_counts(project_id),
            self._stats_repository.get_labeler_class_counts(project_id),
            self._stats_repository.get_daily_label_counts(project_id),
        )

        # class_distribution: aggregate from labeler_class_rows
        class_distribution: dict[str, int] = defaultdict(int)
        for row in labeler_class_rows:
            class_distribution[row.label] += row.count

        # labeler_class_counts: group by labeler
        labeler_map: dict[UUID, LabelerClassCount] = {}
        for row in labeler_class_rows:
            if row.labeler_id not in labeler_map:
                labeler_map[row.labeler_id] = LabelerClassCount(
                    labeler_id=row.labeler_id, username=row.username, counts={}
                )
            labeler_map[row.labeler_id].counts[row.label] = row.count

        # labeler_daily_activity: group by labeler -> day -> label
        daily_by_labeler: dict[UUID, dict[date, dict[str, int]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(int))
        )
        labeler_usernames: dict[UUID, str] = {}
        for row in daily_rows:
            daily_by_labeler[row.labeler_id][row.day][row.label] += row.count
            labeler_usernames[row.labeler_id] = row.username

        labeler_daily_activity = [
            LabelerDailyActivity(
                labeler_id=lid,
                username=labeler_usernames[lid],
                daily=[
                    DailyCount(date=day, counts=dict(labels))
                    for day, labels in sorted(days.items())
                ],
            )
            for lid, days in daily_by_labeler.items()
        ]

        # daily_totals: group by day -> labeler
        day_labeler: dict[date, dict[UUID, DailyLabelerTotal]] = defaultdict(dict)
        for row in daily_rows:
            key = row.labeler_id
            if key not in day_labeler[row.day]:
                day_labeler[row.day][key] = DailyLabelerTotal(
                    labeler_id=row.labeler_id, username=row.username, count=0
                )
            day_labeler[row.day][key].count += row.count

        daily_totals = [
            DailyTotal(date=day, labelers=list(labelers.values()))
            for day, labelers in sorted(day_labeler.items())
        ]

        return ProjectStats(
            total_images=image_counts.total,
            labeled_images=image_counts.labeled,
            class_distribution=dict(class_distribution),
            labeler_class_counts=list(labeler_map.values()),
            labeler_daily_activity=labeler_daily_activity,
            daily_totals=daily_totals,
        )
