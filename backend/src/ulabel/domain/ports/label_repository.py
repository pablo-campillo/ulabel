from abc import ABC, abstractmethod
from uuid import UUID

from ulabel.domain.labels import LabelExportRow, LabelRecord


class LabelRepository(ABC):

    @abstractmethod
    async def save(self, label_record: LabelRecord) -> None:
        raise NotImplementedError

    @abstractmethod
    async def count_by_project(self, project_id: UUID) -> int:
        raise NotImplementedError

    @abstractmethod
    async def get_export_data(self, project_id: UUID) -> list[LabelExportRow]:
        raise NotImplementedError
