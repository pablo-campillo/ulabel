from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from ulabel.domain.images import Image, ImageStatus
from ulabel.infrastructure.models.base import Base


class ImageModel(Base):
    __tablename__ = "images"
    __table_args__ = (
        UniqueConstraint("project_id", "storage_key", name="uq_images_project_storage_key"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True
    )
    storage_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    labeler_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    assignment_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    def to_domain(self) -> Image:
        return Image(
            id=self.id,
            project_id=self.project_id,
            storage_key=self.storage_key,
            status=ImageStatus(self.status),
            labeler_id=self.labeler_id,
            assigned_at=self.assigned_at,
            assignment_id=self.assignment_id,
        )

    @classmethod
    def from_domain(cls, image: Image) -> "ImageModel":
        return cls(
            id=image.id,
            project_id=image.project_id,
            storage_key=image.storage_key,
            status=image.status.value,
            labeler_id=image.labeler_id,
            assigned_at=image.assigned_at,
            assignment_id=image.assignment_id,
        )
