import pytest
from uuid import uuid4
from fastapi.testclient import TestClient

from ulabel.api.main import app
from ulabel.domain.projects import Project
from ulabel.domain.users import User
from ulabel.infrastructure.repositories.in_memory_project_repository import InMemoryProjectRepository
from ulabel.infrastructure.repositories.in_memory_user_repository import InMemoryUserRepository


@pytest.fixture
def admin():
    return User.create_admin(id=uuid4(), username="admin")


@pytest.fixture
def labeler():
    return User.create_labeler(id=uuid4(), username="labeler")


@pytest.fixture
def project(admin):
    return Project.create(id=uuid4(), owner=admin, name="My Project", description="desc", labels={"cat"})


def make_client(users: list[User], projects: list[Project]):
    user_repo = InMemoryUserRepository(users=users)
    project_repo = InMemoryProjectRepository(projects=projects)
    return (
        app.container.user_repository.override(user_repo),
        app.container.project_repository.override(project_repo),
        TestClient(app),
    )


@pytest.fixture
def client(admin, labeler):
    user_ctx, project_ctx, test_client = make_client(users=[admin, labeler], projects=[])
    with user_ctx, project_ctx:
        yield test_client


@pytest.fixture
def client_with_project(admin, labeler, project):
    user_ctx, project_ctx, test_client = make_client(users=[admin, labeler], projects=[project])
    with user_ctx, project_ctx:
        yield test_client


# --- create project ---

def test_create_project_returns_201(client, admin):
    response = client.post("/v1/projects", json={
        "owner_id": str(admin.id),
        "name": "My Project",
        "description": "A test project",
        "labels": ["cat", "dog"],
    })
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "My Project"
    assert body["owner_id"] == str(admin.id)
    assert set(body["labels"]) == {"cat", "dog"}


def test_create_project_returns_404_when_owner_not_found(client):
    response = client.post("/v1/projects", json={
        "owner_id": str(uuid4()),
        "name": "x",
        "description": "x",
        "labels": [],
    })
    assert response.status_code == 404


def test_create_project_returns_403_when_owner_is_not_admin(client, labeler):
    response = client.post("/v1/projects", json={
        "owner_id": str(labeler.id),
        "name": "x",
        "description": "x",
        "labels": [],
    })
    assert response.status_code == 403


# --- add labeler ---

def test_add_labeler_returns_200(client_with_project, project, labeler):
    response = client_with_project.post(f"/v1/projects/{project.id}/labelers", json={
        "labeler_id": str(labeler.id),
    })
    assert response.status_code == 200


def test_add_labeler_returns_404_when_project_not_found(client_with_project, labeler):
    response = client_with_project.post(f"/v1/projects/{uuid4()}/labelers", json={
        "labeler_id": str(labeler.id),
    })
    assert response.status_code == 404


def test_add_labeler_returns_404_when_labeler_not_found(client_with_project, project):
    response = client_with_project.post(f"/v1/projects/{project.id}/labelers", json={
        "labeler_id": str(uuid4()),
    })
    assert response.status_code == 404


def test_add_labeler_returns_403_when_user_is_not_labeler(client_with_project, project, admin):
    response = client_with_project.post(f"/v1/projects/{project.id}/labelers", json={
        "labeler_id": str(admin.id),
    })
    assert response.status_code == 403
