from uuid import UUID, uuid4

from ulabel.application.add_labeler_to_project import ProjectNotFound
from ulabel.domain.errors import DomainError
from ulabel.domain.images import ImageStatus
from ulabel.domain.labels import LabelRecord, LabelerSubmitStats
from ulabel.domain.ports.image_repository import ImageRepository
from ulabel.domain.ports.label_repository import LabelRepository
from ulabel.domain.ports.project_repository import ProjectRepository
from ulabel.domain.ports.stats_repository import StatsRepository


class ImageNotFound(DomainError):
    pass


class ImageNotInProgress(DomainError):
    pass


class AssignmentMismatch(DomainError):
    pass


class LabelerMismatch(DomainError):
    pass


class InvalidLabel(DomainError):
    pass


class SubmitLabelUseCase:

    def __init__(
        self,
        project_repository: ProjectRepository,
        image_repository: ImageRepository,
        label_repository: LabelRepository,
        stats_repository: StatsRepository,
    ):
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
