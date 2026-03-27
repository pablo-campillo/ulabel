from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class UserRole(StrEnum):
    ADMIN = "admin"
    LABELER = "labeler"


@dataclass
class User:
    id: UUID
    username: str
    role: UserRole

    @classmethod
    def create_admin(cls, id: UUID, username: str) -> "User":
        return cls(id=id, username=username, role=UserRole.ADMIN)

    @classmethod
    def create_labeler(cls, id: UUID, username: str) -> "User":
        return cls(id=id, username=username, role=UserRole.LABELER)
