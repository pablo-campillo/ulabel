"""Port interface for project statistics queries."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from ulabel.domain.labels import LabelerSubmitStats


@dataclass
class ImageCounts:
    """Aggregate image counts for a project.

    Attributes:
        total: Total number of images in the project.
        labeled: Number of images that have been labeled.
    """

    total: int
    labeled: int


@dataclass
class LabelerClassRow:
    """Per-labeler, per-label count used in statistics dashboards.

    Attributes:
        labeler_id: Identifier of the labeler.
        username: Display name of the labeler.
        label: The label value.
        count: Number of times this labeler applied this label.
    """

    labeler_id: UUID
    username: str
    label: str
    count: int


@dataclass
class DailyLabelRow:
    """Per-labeler, per-day, per-label count for time-series statistics.

    Attributes:
        labeler_id: Identifier of the labeler.
        username: Display name of the labeler.
        day: The date of the aggregation.
        label: The label value.
        count: Number of labels submitted on that day.
    """

    labeler_id: UUID
    username: str
    day: date
    label: str
    count: int


class StatsRepository(ABC):
    """Abstract repository for querying project and labeler statistics."""

    @abstractmethod
    async def get_image_counts(self, project_id: UUID) -> ImageCounts:
        """Get total and labeled image counts for a project.

        Args:
            project_id: The project to query.

        Returns:
            Aggregate image counts.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_labeler_class_counts(self, project_id: UUID) -> list[LabelerClassRow]:
        """Get label counts broken down by labeler and label value.

        Args:
            project_id: The project to query.

        Returns:
            A list of per-labeler, per-label count rows.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_daily_label_counts(self, project_id: UUID) -> list[DailyLabelRow]:
        """Get label counts broken down by labeler, day, and label value.

        Args:
            project_id: The project to query.

        Returns:
            A list of daily label count rows.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_labeler_ranking(self, project_id: UUID, labeler_id: UUID) -> LabelerSubmitStats:
        """Get submission statistics and ranking for a specific labeler.

        Args:
            project_id: The project to query.
            labeler_id: The labeler to get stats for.

        Returns:
            The labeler's submission count, ranking, and total labeler count.
        """
        raise NotImplementedError
