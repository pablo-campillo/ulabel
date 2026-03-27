from dataclasses import dataclass, field
from uuid import UUID

from ulabel.domain.users import User


@dataclass
class Project:
    id: UUID
    owner: User
    name: str
    description: str
    labels: set[str]
    labeler_ids: set[UUID] = field(default_factory=set)

    @classmethod
    def create(cls, id: UUID, owner: User, name: str, description: str, labels: set[str]) -> "Project":
        return cls(id=id, owner=owner, name=name, description=description, labels=labels)

    def add_labeler(self, labeler_id: UUID) -> None:
        self.labeler_ids.add(labeler_id)
