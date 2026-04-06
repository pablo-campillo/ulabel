from datetime import datetime, timezone
from uuid import uuid4

import pytest

from ulabel.application.add_labeler_to_project import ProjectNotFound
from ulabel.application.submit_label import (
    AssignmentMismatch,
    ImageNotFound,
    ImageNotInProgress,
    InvalidLabel,
    LabelerMismatch,
    SubmitLabelUseCase,
)
from ulabel.domain.images import Image, ImageStatus
from ulabel.domain.projects import Project
from ulabel.infrastructure.repositories.in_memory.image_repository import InMemoryImageRepository
from ulabel.infrastructure.repositories.in_memory.label_repository import InMemoryLabelRepository
from ulabel.infrastructure.repositories.in_memory.project_repository import (
    InMemoryProjectRepository,
)
from ulabel.infrastructure.repositories.in_memory.stats_repository import InMemoryStatsRepository

FIXED_NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def project(admin, labeler):
    p = Project.create(
        id=uuid4(), owner=admin, name="Project", description="desc", labels={"cat", "dog"}
    )
    p.add_labeler(labeler.id)
    return p


@pytest.fixture
def assigned_image(project, labeler):
    img = Image.create(id=uuid4(), project_id=project.id, storage_key="img.jpg")
    img.assign(labeler_id=labeler.id, assigned_at=FIXED_NOW)
    return img


@pytest.fixture
def use_case(project, assigned_image, labeler):
    images = [assigned_image]
    labels = []
    return SubmitLabelUseCase(
        project_repository=InMemoryProjectRepository(projects=[project]),
        image_repository=InMemoryImageRepository(images=images),
        label_repository=InMemoryLabelRepository(),
        stats_repository=InMemoryStatsRepository(
            images=images,
            labels=labels,
            usernames={labeler.id: labeler.username},
        ),
    )


async def test_submit_label_creates_record(use_case, project, assigned_image, labeler):
    record, stats = await use_case.execute(
        project_id=project.id,
        image_id=assigned_image.id,
        labeler_id=labeler.id,
        assignment_id=assigned_image.assignment_id,
        label="cat",
    )
    assert record.project_id == project.id
    assert record.image_id == assigned_image.id
    assert record.labeler_id == labeler.id
    assert record.label == "cat"
    assert stats.ranking >= 1


async def test_submit_label_marks_image_done(use_case, project, assigned_image, labeler):
    _ = await use_case.execute(
        project_id=project.id,
        image_id=assigned_image.id,
        labeler_id=labeler.id,
        assignment_id=assigned_image.assignment_id,
        label="cat",
    )
    assert assigned_image.status == ImageStatus.DONE


async def test_raises_when_project_not_found(use_case, assigned_image, labeler):
    with pytest.raises(ProjectNotFound):
        await use_case.execute(
            project_id=uuid4(),
            image_id=assigned_image.id,
            labeler_id=labeler.id,
            assignment_id=assigned_image.assignment_id,
            label="cat",
        )


async def test_raises_when_image_not_found(use_case, project, labeler, assigned_image):
    with pytest.raises(ImageNotFound):
        await use_case.execute(
            project_id=project.id,
            image_id=uuid4(),
            labeler_id=labeler.id,
            assignment_id=assigned_image.assignment_id,
            label="cat",
        )


async def test_raises_when_image_not_in_project(project, labeler):
    other_image = Image.create(id=uuid4(), project_id=uuid4(), storage_key="other.jpg")
    other_image.assign(labeler_id=labeler.id, assigned_at=FIXED_NOW)
    use_case = SubmitLabelUseCase(
        project_repository=InMemoryProjectRepository(projects=[project]),
        image_repository=InMemoryImageRepository(images=[other_image]),
        label_repository=InMemoryLabelRepository(),
        stats_repository=InMemoryStatsRepository(images=[other_image], labels=[], usernames={}),
    )
    with pytest.raises(ImageNotFound):
        await use_case.execute(
            project_id=project.id,
            image_id=other_image.id,
            labeler_id=labeler.id,
            assignment_id=other_image.assignment_id,
            label="cat",
        )


async def test_raises_when_image_is_pending(project, labeler):
    pending_image = Image.create(id=uuid4(), project_id=project.id, storage_key="img.jpg")
    use_case = SubmitLabelUseCase(
        project_repository=InMemoryProjectRepository(projects=[project]),
        image_repository=InMemoryImageRepository(images=[pending_image]),
        label_repository=InMemoryLabelRepository(),
        stats_repository=InMemoryStatsRepository(images=[pending_image], labels=[], usernames={}),
    )
    with pytest.raises(ImageNotInProgress):
        await use_case.execute(
            project_id=project.id,
            image_id=pending_image.id,
            labeler_id=labeler.id,
            assignment_id=uuid4(),
            label="cat",
        )


async def test_raises_when_image_already_done(project, labeler):
    done_image = Image.create(id=uuid4(), project_id=project.id, storage_key="img.jpg")
    done_image.assign(labeler_id=labeler.id, assigned_at=FIXED_NOW)
    done_image.complete()
    use_case = SubmitLabelUseCase(
        project_repository=InMemoryProjectRepository(projects=[project]),
        image_repository=InMemoryImageRepository(images=[done_image]),
        label_repository=InMemoryLabelRepository(),
        stats_repository=InMemoryStatsRepository(images=[done_image], labels=[], usernames={}),
    )
    with pytest.raises(ImageNotInProgress):
        await use_case.execute(
            project_id=project.id,
            image_id=done_image.id,
            labeler_id=labeler.id,
            assignment_id=done_image.assignment_id,
            label="cat",
        )


async def test_raises_when_assignment_id_mismatch(use_case, project, assigned_image, labeler):
    with pytest.raises(AssignmentMismatch):
        await use_case.execute(
            project_id=project.id,
            image_id=assigned_image.id,
            labeler_id=labeler.id,
            assignment_id=uuid4(),
            label="cat",
        )


async def test_raises_when_labeler_id_mismatch(use_case, project, assigned_image):
    with pytest.raises(LabelerMismatch):
        await use_case.execute(
            project_id=project.id,
            image_id=assigned_image.id,
            labeler_id=uuid4(),
            assignment_id=assigned_image.assignment_id,
            label="cat",
        )


async def test_raises_when_label_not_in_project(use_case, project, assigned_image, labeler):
    with pytest.raises(InvalidLabel):
        await use_case.execute(
            project_id=project.id,
            image_id=assigned_image.id,
            labeler_id=labeler.id,
            assignment_id=assigned_image.assignment_id,
            label="airplane",
        )
