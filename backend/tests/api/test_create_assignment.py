from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from ulabel.api.main import app
from ulabel.domain.images import Image
from ulabel.domain.projects import Project
from ulabel.domain.users import User
from ulabel.infrastructure.repositories.in_memory_image_repository import InMemoryImageRepository
from ulabel.infrastructure.repositories.in_memory_project_repository import (
    InMemoryProjectRepository,
)
from ulabel.infrastructure.storage.fake_storage_service import FakeStorageService

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
def client(project, pending_image):
    image_repo = InMemoryImageRepository(images=[pending_image])
    with (
        app.container.project_repository.override(InMemoryProjectRepository(projects=[project])),
        app.container.image_repository.override(image_repo),
        app.container.storage_service.override(FakeStorageService()),
    ):
        yield TestClient(app)


def test_create_assignment_returns_201(client, project, labeler, pending_image):
    url = f"/v1/projects/{project.id}/assignments"
    response = client.post(url, json={"labeler_id": str(labeler.id)})
    assert response.status_code == 201
    body = response.json()
    assert body["id"] == str(pending_image.id)
    assert body["status"] == "in_progress"
    assert body["assignment_id"] is not None


def test_create_assignment_returns_presigned_url(client, project, labeler, pending_image):
    url = f"/v1/projects/{project.id}/assignments"
    response = client.post(url, json={"labeler_id": str(labeler.id)})
    body = response.json()
    assert "presigned_url" in body
    assert "img.jpg" in body["presigned_url"]
    assert body["presigned_url_expires_in"] == 60


def test_create_assignment_returns_404_when_project_not_found(client, labeler):
    url = f"/v1/projects/{uuid4()}/assignments"
    response = client.post(url, json={"labeler_id": str(labeler.id)})
    assert response.status_code == 404


def test_create_assignment_returns_403_when_labeler_not_in_project(client, project):
    url = f"/v1/projects/{project.id}/assignments"
    response = client.post(url, json={"labeler_id": str(uuid4())})
    assert response.status_code == 403


def test_create_assignment_returns_204_when_no_images_available(project, labeler):
    with (
        app.container.project_repository.override(InMemoryProjectRepository(projects=[project])),
        app.container.image_repository.override(InMemoryImageRepository(images=[])),
        app.container.storage_service.override(FakeStorageService()),
    ):
        response = TestClient(app).post(
            f"/v1/projects/{project.id}/assignments",
            json={"labeler_id": str(labeler.id)},
        )
    assert response.status_code == 204
