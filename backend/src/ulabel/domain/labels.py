from dataclasses import dataclass
from uuid import UUID


@dataclass
class LabelRecord:
    id: UUID
    project_id: UUID
    image_id: UUID
    labeler_id: UUID
    label: str

    @classmethod
    def create(
        cls, id: UUID, project_id: UUID, image_id: UUID, labeler_id: UUID, label: str
    ) -> "LabelRecord":
        return cls(
            id=id, project_id=project_id, image_id=image_id, labeler_id=labeler_id, label=label
        )


@dataclass
class LabelExportRow:
    image_id: UUID
    storage_key: str
    value: str
