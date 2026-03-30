"""Domain models for labels, export data, and labeler statistics."""

from dataclasses import dataclass
from uuid import UUID


@dataclass
class LabelRecord:
    """A label applied by a labeler to an image within a project.

    Attributes:
        id: Unique identifier for this label record.
        project_id: Identifier of the project the label belongs to.
        image_id: Identifier of the labeled image.
        labeler_id: Identifier of the labeler who created the label.
        label: The label value assigned to the image.
    """

    id: UUID
    project_id: UUID
    image_id: UUID
    labeler_id: UUID
    label: str

    @classmethod
    def create(
        cls, id: UUID, project_id: UUID, image_id: UUID, labeler_id: UUID, label: str
    ) -> "LabelRecord":
        """Create a new label record.

        Args:
            id: Unique identifier for the record.
            project_id: Identifier of the owning project.
            image_id: Identifier of the labeled image.
            labeler_id: Identifier of the labeler.
            label: The label value.

        Returns:
            A new LabelRecord instance.
        """
        return cls(
            id=id, project_id=project_id, image_id=image_id, labeler_id=labeler_id, label=label
        )


@dataclass
class LabelExportRow:
    """A flattened row used when exporting labels for a project.

    Attributes:
        image_id: Identifier of the image.
        storage_key: Object-storage key of the image file.
        value: The label value assigned to the image.
    """

    image_id: UUID
    storage_key: str
    value: str


@dataclass
class LabelerSubmitStats:
    """Statistics about a labeler's submissions within a project.

    Attributes:
        labeler_count: Number of labels submitted by the labeler.
        ranking: The labeler's rank among all labelers in the project.
        total_labelers: Total number of labelers in the project.
    """

    labeler_count: int
    ranking: int
    total_labelers: int
