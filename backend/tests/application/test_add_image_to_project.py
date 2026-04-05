from uuid import uuid4

import pytest

from ulabel.application.add_image_to_project import AddImageToProjectUseCase
from ulabel.application.add_labeler_to_project import ProjectNotFound
from ulabel.domain.images import ImageStatus
from ulabel.domain.projects import Project
from ulabel.domain.users import User
from ulabel.infrastructure.repositories.in_memory_image_repository import InMemoryImageRepository
from ulabel.infrastructure.repositories.in_memory_project_repository import (
    InMemoryProjectRepository,
)


@pytest.fixture
def admin():
    return User.create_admin(id=uuid4(), username="admin")


@pytest.fixture
def project(admin):
    return Project.create(
        id=uuid4(), owner=admin, name="My Project",
        description="desc", labels={"cat"},
    )


@pytest.fixture
def use_case(project):
    return AddImageToProjectUseCase(
        project_repository=InMemoryProjectRepository(projects=[project]),
        image_repository=InMemoryImageRepository(),
    )


async def test_add_image_returns_image_with_correct_project(use_case, project):
    image = await use_case.execute(project_id=project.id, storage_key="images/photo.jpg")
    assert image.project_id == project.id
    assert image.storage_key == "images/photo.jpg"


async def test_add_image_returns_image_with_pending_status(use_case, project):
    image = await use_case.execute(project_id=project.id, storage_key="images/photo.jpg")
    assert image.status == ImageStatus.PENDING


async def test_add_image_raises_when_project_not_found(use_case):
    with pytest.raises(ProjectNotFound):
        await use_case.execute(project_id=uuid4(), storage_key="images/photo.jpg")
