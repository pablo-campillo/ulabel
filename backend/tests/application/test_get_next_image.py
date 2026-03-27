import pytest
from datetime import datetime, timezone
from uuid import uuid4

from ulabel.application.add_labeler_to_project import ProjectNotFound
from ulabel.application.get_next_image import GetNextImageUseCase, LabelerNotInProject, NoImageAvailable
from ulabel.domain.images import Image, ImageStatus
from ulabel.domain.projects import Project
from ulabel.domain.users import User
from ulabel.infrastructure.repositories.in_memory_image_repository import InMemoryImageRepository
from ulabel.infrastructure.repositories.in_memory_project_repository import InMemoryProjectRepository

FIXED_NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def admin():
    return User.create_admin(id=uuid4(), username="admin")


@pytest.fixture
def labeler():
    return User.create_labeler(id=uuid4(), username="labeler")


@pytest.fixture
def project(admin, labeler):
    p = Project.create(id=uuid4(), owner=admin, name="Project", description="desc", labels={"cat"})
    p.add_labeler(labeler.id)
    return p


@pytest.fixture
def pending_image(project):
    return Image.create(id=uuid4(), project_id=project.id, storage_key="img.jpg")


@pytest.fixture
def use_case(project, pending_image):
    return GetNextImageUseCase(
        project_repository=InMemoryProjectRepository(projects=[project]),
        image_repository=InMemoryImageRepository(images=[pending_image]),
        now=lambda: FIXED_NOW,
    )


async def test_returns_image_assigned_to_labeler(use_case, project, labeler, pending_image):
    image = await use_case.execute(project_id=project.id, labeler_id=labeler.id)
    assert image.id == pending_image.id
    assert image.labeler_id == labeler.id
    assert image.status == ImageStatus.IN_PROGRESS
    assert image.assigned_at == FIXED_NOW
    assert image.assignment_id is not None


async def test_raises_when_project_not_found(use_case, labeler):
    with pytest.raises(ProjectNotFound):
        await use_case.execute(project_id=uuid4(), labeler_id=labeler.id)


async def test_raises_when_labeler_not_in_project(use_case, project):
    with pytest.raises(LabelerNotInProject):
        await use_case.execute(project_id=project.id, labeler_id=uuid4())


async def test_returns_pending_image_with_lowest_uuid(project, labeler):
    from uuid import UUID

    high_id = UUID("ffffffff-ffff-4fff-bfff-ffffffffffff")
    low_id = UUID("00000000-0000-4000-8000-000000000000")
    image_high = Image.create(id=high_id, project_id=project.id, storage_key="high.jpg")
    image_low = Image.create(id=low_id, project_id=project.id, storage_key="low.jpg")

    use_case = GetNextImageUseCase(
        project_repository=InMemoryProjectRepository(projects=[project]),
        image_repository=InMemoryImageRepository(images=[image_high, image_low]),
        now=lambda: FIXED_NOW,
    )

    image = await use_case.execute(project_id=project.id, labeler_id=labeler.id)
    assert image.id == low_id


async def test_raises_when_no_pending_images(project, labeler):
    use_case = GetNextImageUseCase(
        project_repository=InMemoryProjectRepository(projects=[project]),
        image_repository=InMemoryImageRepository(),
        now=lambda: FIXED_NOW,
    )
    with pytest.raises(NoImageAvailable):
        await use_case.execute(project_id=project.id, labeler_id=labeler.id)
