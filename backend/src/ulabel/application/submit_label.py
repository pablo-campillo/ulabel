from uuid import UUID, uuid4

from ulabel.application.add_labeler_to_project import ProjectNotFound
from ulabel.domain.images import ImageStatus
from ulabel.domain.labels import LabelRecord
from ulabel.domain.ports.image_repository import ImageRepository
from ulabel.domain.ports.label_repository import LabelRepository
from ulabel.domain.ports.project_repository import ProjectRepository


class ImageNotFound(Exception):
    pass


class ImageNotInProgress(Exception):
    pass


class AssignmentMismatch(Exception):
    pass


class LabelerMismatch(Exception):
    pass


class InvalidLabel(Exception):
    pass


class SubmitLabelUseCase:

    def __init__(
        self,
        project_repository: ProjectRepository,
        image_repository: ImageRepository,
        label_repository: LabelRepository,
    ):
        self.project_repository = project_repository
        self.image_repository = image_repository
        self.label_repository = label_repository

    async def execute(
        self,
        project_id: UUID,
        image_id: UUID,
        labeler_id: UUID,
        assignment_id: UUID,
        label: str,
    ) -> LabelRecord:
        project = await self.project_repository.get_by_id(project_id)
        if project is None:
            raise ProjectNotFound(f"Project '{project_id}' not found")

        image = await self.image_repository.get_by_id(image_id)
        if image is None or image.project_id != project_id:
            raise ImageNotFound(f"Image '{image_id}' not found in project '{project_id}'")

        if image.status != ImageStatus.IN_PROGRESS:
            raise ImageNotInProgress(
                f"Image '{image_id}' is not in progress (status: {image.status})"
            )

        if image.assignment_id != assignment_id:
            raise AssignmentMismatch(
                f"Assignment ID mismatch for image '{image_id}'"
            )

        if image.labeler_id != labeler_id:
            raise LabelerMismatch(
                f"Labeler '{labeler_id}' is not assigned to image '{image_id}'"
            )

        if label not in project.labels:
            raise InvalidLabel(
                f"Label '{label}' is not valid for project '{project_id}'. "
                f"Valid labels: {project.labels}"
            )

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

        return label_record
