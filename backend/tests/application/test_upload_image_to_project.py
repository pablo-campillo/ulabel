from uuid import uuid4

import pytest

from ulabel.application.add_labeler_to_project import ProjectNotFound
from ulabel.application.upload_image_to_project import UploadImageToProjectUseCase
from ulabel.domain.images import ImageStatus
from ulabel.domain.projects import Project
from ulabel.domain.users import User
from ulabel.infrastructure.repositories.in_memory_image_repository import InMemoryImageRepository
from ulabel.infrastructure.repositories.in_memory_project_repository import (
    InMemoryProjectRepository,
)
from ulabel.infrastructure.storage.fake_storage_service import FakeStorageService


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
    return UploadImageToProjectUseCase(
        project_repository=InMemoryProjectRepository(projects=[project]),
        image_repository=InMemoryImageRepository(),
        storage_service=FakeStorageService(),
    )


async def test_upload_image_returns_image_with_correct_project(use_case, project):
    image = await use_case.execute(
        project_id=project.id, data=b"fake-image",
        content_type="image/jpeg",
    )
    assert image.project_id == project.id


async def test_upload_image_returns_image_with_pending_status(use_case, project):
    image = await use_case.execute(
        project_id=project.id, data=b"fake-image",
        content_type="image/jpeg",
    )
    assert image.status == ImageStatus.PENDING


async def test_upload_image_storage_key_contains_project_id(use_case, project):
    image = await use_case.execute(
        project_id=project.id, data=b"fake-image",
        content_type="image/jpeg",
    )
    assert str(project.id) in image.storage_key


async def test_upload_image_raises_when_project_not_found(use_case):
    with pytest.raises(ProjectNotFound):
        await use_case.execute(
            project_id=uuid4(), data=b"fake-image",
            content_type="image/jpeg",
        )
