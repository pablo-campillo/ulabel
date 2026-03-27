from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from ulabel.domain.labels import LabelRecord
from ulabel.infrastructure.models.base import Base


class LabelRecordModel(Base):
    __tablename__ = "label_records"
    __table_args__ = (
        UniqueConstraint("image_id", name="uq_label_records_image_id"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True
    )
    image_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("images.id"), nullable=False
    )
    labeler_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def to_domain(self) -> LabelRecord:
        return LabelRecord(
            id=self.id,
            project_id=self.project_id,
            image_id=self.image_id,
            labeler_id=self.labeler_id,
            label=self.label,
        )

    @classmethod
    def from_domain(cls, label_record: LabelRecord) -> "LabelRecordModel":
        return cls(
            id=label_record.id,
            project_id=label_record.project_id,
            image_id=label_record.image_id,
            labeler_id=label_record.labeler_id,
            label=label_record.label,
        )
