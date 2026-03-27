from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID

from ulabel.domain.users import User


@dataclass
class Project:
    id: UUID
    owner: User
    name: str
    description: str
    labels: set[str]
    created_at: datetime | None = None
    labeler_ids: set[UUID] = field(default_factory=set)

    @classmethod
    def create(cls, id: UUID, owner: User, name: str, description: str, labels: set[str], created_at: datetime | None = None) -> "Project":
        if created_at is None:
            created_at = datetime.now(timezone.utc)
        return cls(id=id, owner=owner, name=name, description=description, labels=labels, created_at=created_at)

    def add_labeler(self, labeler_id: UUID) -> None:
        self.labeler_ids.add(labeler_id)
