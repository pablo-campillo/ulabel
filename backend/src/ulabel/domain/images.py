"""Domain model for images within labeling projects."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4


class ImageStatus(StrEnum):
    """Possible lifecycle states of an image in the labeling workflow."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"


@dataclass
class Image:
    """An image that belongs to a project and moves through the labeling workflow.

    Attributes:
        id: Unique identifier for the image.
        project_id: Identifier of the project this image belongs to.
        storage_key: Object-storage key used to locate the image file.
        status: Current lifecycle status of the image.
        labeler_id: Identifier of the labeler currently assigned, if any.
        assigned_at: Timestamp when the image was assigned to a labeler.
        assignment_id: Unique identifier for the current assignment session.
    """

    id: UUID
    project_id: UUID
    storage_key: str
    status: ImageStatus = ImageStatus.PENDING
    labeler_id: UUID | None = None
    assigned_at: datetime | None = None
    assignment_id: UUID | None = None

    @classmethod
    def create(cls, id: UUID, project_id: UUID, storage_key: str) -> "Image":
        """Create a new image in PENDING status.

        Args:
            id: Unique identifier for the image.
            project_id: Identifier of the owning project.
            storage_key: Object-storage key for the image file.

        Returns:
            A new Image instance with default PENDING status.
        """
        return cls(id=id, project_id=project_id, storage_key=storage_key)

    def assign(self, labeler_id: UUID, assigned_at: datetime) -> None:
        """Assign the image to a labeler and transition to IN_PROGRESS.

        Args:
            labeler_id: Identifier of the labeler receiving the assignment.
            assigned_at: Timestamp of the assignment.
        """
        self.labeler_id = labeler_id
        self.assigned_at = assigned_at
        self.assignment_id = uuid4()
        self.status = ImageStatus.IN_PROGRESS

    def complete(self) -> None:
        """Mark the image as fully labeled by transitioning to DONE."""
        self.status = ImageStatus.DONE

    def expire(self) -> None:
        """Reset the image back to PENDING, clearing its assignment data."""
        self.status = ImageStatus.PENDING
        self.labeler_id = None
        self.assigned_at = None
        self.assignment_id = None
