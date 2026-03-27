from uuid import UUID

from ulabel.domain.labels import LabelExportRow, LabelRecord
from ulabel.domain.ports.label_repository import LabelRepository


class InMemoryLabelRepository(LabelRepository):

    def __init__(self) -> None:
        self._records: dict[UUID, LabelRecord] = {}

    async def save(self, label_record: LabelRecord) -> None:
        self._records[label_record.id] = label_record

    async def count_by_project(self, project_id: UUID) -> int:
        return sum(1 for r in self._records.values() if r.project_id == project_id)

    async def get_export_data(self, project_id: UUID) -> list[LabelExportRow]:
        return [
            LabelExportRow(image_id=r.image_id, storage_key="", value=r.label)
            for r in self._records.values()
            if r.project_id == project_id
        ]
