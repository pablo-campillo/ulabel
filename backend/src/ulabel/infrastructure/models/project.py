"""SQLAlchemy ORM models for projects and their associations.

Maps the ``projects``, ``project_labels``, and ``project_labelers``
tables and provides conversion to/from domain Project entities.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ulabel.domain.projects import Project
from ulabel.infrastructure.models.base import Base
from ulabel.infrastructure.models.user import UserModel


class ProjectLabelModel(Base):
    """Association model linking a project to one of its allowed labels."""

    __tablename__ = "project_labels"

    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    label: Mapped[str] = mapped_column(String(255), primary_key=True)


class ProjectLabelerModel(Base):
    """Association model linking a project to an assigned labeler."""

    __tablename__ = "project_labelers"
    __table_args__ = (Index("ix_project_labelers_labeler_id", "labeler_id"),)

    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    labeler_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)


class ProjectModel(Base):
    """ORM model representing a labelling project with its labels and labelers."""

    __tablename__ = "projects"
    __table_args__ = (
        Index("ix_projects_created_at", "created_at", postgresql_ops={"created_at": "DESC"}),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    owner_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    owner: Mapped[UserModel] = relationship("UserModel", lazy="joined")
    label_entries: Mapped[list[ProjectLabelModel]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )
    labeler_entries: Mapped[list[ProjectLabelerModel]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )

    def to_domain(self) -> Project:
        """Convert this ORM model to a domain Project entity.

        Returns:
            The corresponding domain Project with labels and labeler IDs.
        """
        return Project(
            id=self.id,
            owner=self.owner.to_domain(),
            name=self.name,
            description=self.description,
            labels={e.label for e in self.label_entries},
            created_at=self.created_at,
            labeler_ids={e.labeler_id for e in self.labeler_entries},
        )

    @classmethod
    def from_domain(cls, project: Project) -> "ProjectModel":
        """Create an ORM model from a domain Project entity.

        Args:
            project: The domain Project to convert.

        Returns:
            A new ProjectModel with associated label and labeler entries.
        """
        model = cls(
            id=project.id,
            owner_id=project.owner.id,
            name=project.name,
            description=project.description,
            created_at=project.created_at,
        )
        model.label_entries = [
            ProjectLabelModel(project_id=project.id, label=label) for label in project.labels
        ]
        model.labeler_entries = [
            ProjectLabelerModel(project_id=project.id, labeler_id=lid)
            for lid in project.labeler_ids
        ]
        return model
