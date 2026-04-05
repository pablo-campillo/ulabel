"""Use case for submitting a label for an assigned image."""

from uuid import UUID, uuid4

from ulabel.application.add_labeler_to_project import ProjectNotFound
from ulabel.domain.errors import DomainError
from ulabel.domain.images import ImageStatus
from ulabel.domain.labels import LabelerSubmitStats, LabelRecord
from ulabel.domain.ports.image_repository import ImageRepository
from ulabel.domain.ports.label_repository import LabelRepository
from ulabel.domain.ports.project_repository import ProjectRepository
from ulabel.domain.ports.stats_repository import StatsRepository


class ImageNotFound(DomainError):
    """Raised when the image does not exist or does not belong to the project."""

    pass


class ImageNotInProgress(DomainError):
    """Raised when the image is not in the in-progress state."""

    pass


class AssignmentMismatch(DomainError):
    """Raised when the provided assignment ID does not match the image's assignment."""

    pass


class LabelerMismatch(DomainError):
    """Raised when the submitting labeler does not match the assigned labeler."""

    pass


class InvalidLabel(DomainError):
    """Raised when the submitted label value is not in the project's allowed labels."""

    pass


class SubmitLabelUseCase:
    """Records a label for an assigned image and returns updated labeler stats.

    Validates the full assignment chain (project, image, assignment, labeler,
    label value) before persisting the label and marking the image as complete.
    """

    def __init__(
        self,
        project_repository: ProjectRepository,
        image_repository: ImageRepository,
        label_repository: LabelRepository,
        stats_repository: StatsRepository,
    ):
        """Initialize the use case.

        Args:
            project_repository: Repository for project lookups.
            image_repository: Repository for image lookups and persistence.
            label_repository: Repository for label persistence.
            stats_repository: Repository for labeler ranking queries.
        """
        self.project_repository = project_repository
        self.image_repository = image_repository
        self.label_repository = label_repository
        self.stats_repository = stats_repository

    async def execute(
        self,
        project_id: UUID,
        image_id: UUID,
        labeler_id: UUID,
        assignment_id: UUID,
        label: str,
    ) -> tuple[LabelRecord, LabelerSubmitStats]:
        """Submit a label for an assigned image.

        Args:
            project_id: The project the image belongs to.
            image_id: The image being labeled.
            labeler_id: The labeler submitting the label.
            assignment_id: The assignment ID to verify ownership.
            label: The label value to assign.

        Returns:
            A tuple of the created label record and the labeler's updated stats.

        Raises:
            ProjectNotFound: If the project does not exist.
            ImageNotFound: If the image does not exist or is in another project.
            ImageNotInProgress: If the image is not currently assigned.
            AssignmentMismatch: If the assignment ID does not match.
            LabelerMismatch: If the labeler does not match the assignment.
            InvalidLabel: If the label is not in the project's allowed set.
        """
        project = await self.project_repository.get_by_id(project_id)
        if project is None:
            raise ProjectNotFound("Project not found")

        image = await self.image_repository.get_by_id(image_id)
        if image is None or image.project_id != project_id:
            raise ImageNotFound("Image not found")

        if image.status != ImageStatus.IN_PROGRESS:
            raise ImageNotInProgress("Image is not in progress")

        if image.assignment_id != assignment_id:
            raise AssignmentMismatch("Assignment ID mismatch")

        if image.labeler_id != labeler_id:
            raise LabelerMismatch("Labeler mismatch")

        if label not in project.labels:
            raise InvalidLabel("Invalid label")

        label_record = LabelRecord.create(
            id=uuid4(),
            project_id=project_id,
            image_id=image_id,
            labeler_id=labeler_id,
            label=label,
        )
        await self.label_repository.save(label_record)

        image.complete()
        await self.image_repository.save(image)

        stats = await self.stats_repository.get_labeler_ranking(project_id, labeler_id)

        return label_record, stats
