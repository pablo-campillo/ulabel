from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4


class ImageStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"


@dataclass
class Image:
    id: UUID
    project_id: UUID
    storage_key: str
    status: ImageStatus = ImageStatus.PENDING
    labeler_id: UUID | None = None
    assigned_at: datetime | None = None
    assignment_id: UUID | None = None

    @classmethod
    def create(cls, id: UUID, project_id: UUID, storage_key: str) -> "Image":
        return cls(id=id, project_id=project_id, storage_key=storage_key)

    def assign(self, labeler_id: UUID, assigned_at: datetime) -> None:
        self.labeler_id = labeler_id
        self.assigned_at = assigned_at
        self.assignment_id = uuid4()
        self.status = ImageStatus.IN_PROGRESS

    def complete(self) -> None:
        self.status = ImageStatus.DONE

    def expire(self) -> None:
        self.status = ImageStatus.PENDING
        self.labeler_id = None
        self.assigned_at = None
        self.assignment_id = None
