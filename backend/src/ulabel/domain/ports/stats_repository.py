from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from ulabel.domain.labels import LabelerSubmitStats


@dataclass
class ImageCounts:
    total: int
    labeled: int


@dataclass
class LabelerClassRow:
    labeler_id: UUID
    username: str
    label: str
    count: int


@dataclass
class DailyLabelRow:
    labeler_id: UUID
    username: str
    day: date
    label: str
    count: int


class StatsRepository(ABC):

    @abstractmethod
    async def get_image_counts(self, project_id: UUID) -> ImageCounts:
        raise NotImplementedError

    @abstractmethod
    async def get_labeler_class_counts(self, project_id: UUID) -> list[LabelerClassRow]:
        raise NotImplementedError

    @abstractmethod
    async def get_daily_label_counts(self, project_id: UUID) -> list[DailyLabelRow]:
        raise NotImplementedError

    @abstractmethod
    async def get_labeler_ranking(self, project_id: UUID, labeler_id: UUID) -> LabelerSubmitStats:
        raise NotImplementedError
