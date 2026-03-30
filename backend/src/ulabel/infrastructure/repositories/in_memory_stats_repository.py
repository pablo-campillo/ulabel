"""In-memory implementation of the statistics repository for testing."""

from collections import defaultdict
from uuid import UUID

from ulabel.domain.images import Image, ImageStatus
from ulabel.domain.labels import LabelRecord, LabelerSubmitStats
from ulabel.domain.ports.stats_repository import (
    DailyLabelRow,
    ImageCounts,
    LabelerClassRow,
    StatsRepository,
)


class InMemoryStatsRepository(StatsRepository):
    """In-memory implementation for testing. Operates on shared lists."""

    def __init__(
        self,
        images: list[Image],
        labels: list[LabelRecord],
        usernames: dict[UUID, str],
    ):
        """Initialize with shared data collections.

        Args:
            images: Shared list of images to compute stats from.
            labels: Shared list of label records.
            usernames: Mapping of user IDs to usernames.
        """
        self._images = images
        self._labels = labels
        self._usernames = usernames

    async def get_image_counts(self, project_id: UUID) -> ImageCounts:
        project_images = [i for i in self._images if i.project_id == project_id]
        total = len(project_images)
        labeled = sum(1 for i in project_images if i.status == ImageStatus.DONE)
        return ImageCounts(total=total, labeled=labeled)

    async def get_labeler_class_counts(self, project_id: UUID) -> list[LabelerClassRow]:
        counts: dict[tuple[UUID, str], int] = defaultdict(int)
        for lr in self._labels:
            if lr.project_id == project_id:
                counts[(lr.labeler_id, lr.label)] += 1
        return [
            LabelerClassRow(
                labeler_id=lid,
                username=self._usernames.get(lid, "unknown"),
                label=label,
                count=cnt,
            )
            for (lid, label), cnt in counts.items()
        ]

    async def get_daily_label_counts(self, project_id: UUID) -> list[DailyLabelRow]:
        # In-memory labels don't have created_at, so this returns an empty list.
        return []

    async def get_labeler_ranking(self, project_id: UUID, labeler_id: UUID) -> LabelerSubmitStats:
        counts: dict[UUID, int] = defaultdict(int)
        for lr in self._labels:
            if lr.project_id == project_id:
                counts[lr.labeler_id] += 1
        labeler_count = counts.get(labeler_id, 0)
        total_labelers = len(counts)
        above = sum(1 for c in counts.values() if c > labeler_count)
        ranking = above + 1
        return LabelerSubmitStats(
            labeler_count=labeler_count,
            ranking=ranking,
            total_labelers=total_labelers,
        )
