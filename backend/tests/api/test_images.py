import pytest
from uuid import uuid4
from fastapi.testclient import TestClient

from ulabel.api.main import app
from ulabel.domain.projects import Project
from ulabel.domain.users import User
from ulabel.infrastructure.repositories.in_memory_image_repository import InMemoryImageRepository
from ulabel.infrastructure.repositories.in_memory_project_repository import InMemoryProjectRepository


@pytest.fixture
def admin():
    return User.create_admin(id=uuid4(), username="admin")


@pytest.fixture
def project(admin):
    return Project.create(id=uuid4(), owner=admin, name="My Project", description="desc", labels={"cat"})


@pytest.fixture
def client(project):
    with (
        app.container.project_repository.override(InMemoryProjectRepository(projects=[project])),
        app.container.image_repository.override(InMemoryImageRepository()),
    ):
        yield TestClient(app)


def test_add_image_returns_201(client, project):
    response = client.post(f"/v1/projects/{project.id}/images", json={
        "storage_key": "images/photo.jpg",
    })
    assert response.status_code == 201
    body = response.json()
    assert body["project_id"] == str(project.id)
    assert body["storage_key"] == "images/photo.jpg"
    assert body["status"] == "pending"


def test_add_image_returns_404_when_project_not_found(client):
    response = client.post(f"/v1/projects/{uuid4()}/images", json={
        "storage_key": "images/photo.jpg",
    })
    assert response.status_code == 404
