from uuid import UUID

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from ulabel.domain.users import User, UserRole
from ulabel.infrastructure.models.base import Base


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)

    def to_domain(self) -> User:
        return User(id=self.id, username=self.username, role=UserRole(self.role))

    @classmethod
    def from_domain(cls, user: User) -> "UserModel":
        return cls(id=user.id, username=user.username, role=user.role.value)
