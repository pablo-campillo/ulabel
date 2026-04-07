from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from tests.unit.conftest import make_uow
from ulabel.api.main import app
from ulabel.domain.projects import Project
from ulabel.infrastructure.repositories.in_memory.image_repository import InMemoryImageRepository
from ulabel.infrastructure.repositories.in_memory.project_repository import (
    InMemoryProjectRepository,
)
from ulabel.infrastructure.storage.fake_storage_service import FakeStorageService


@pytest.fixture
def project(admin):
    return Project.create(
        id=uuid4(),
        owner=admin,
        name="My Project",
        description="desc",
        labels={"cat"},
    )


@pytest.fixture
def client(project):
    uow = make_uow(
        project_repository=InMemoryProjectRepository(projects=[project]),
        image_repository=InMemoryImageRepository(),
    )
    with (
        app.container.unit_of_work.override(uow),
        app.container.storage_service.override(FakeStorageService()),
    ):
        yield TestClient(app)


def test_upload_image_returns_201(client, project):
    response = client.post(
        f"/v1/projects/{project.id}/images/upload",
        files={"file": ("photo.jpg", b"fake-image-data", "image/jpeg")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["project_id"] == str(project.id)
    assert str(project.id) in body["storage_key"]
    assert body["status"] == "pending"


def test_upload_image_returns_404_when_project_not_found(client):
    response = client.post(
        f"/v1/projects/{uuid4()}/images/upload",
        files={"file": ("photo.jpg", b"fake-image-data", "image/jpeg")},
    )
    assert response.status_code == 404
