import pytest
from datetime import datetime, timezone
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


# --- list projects ---

def test_list_projects_returns_labeler_count(admin, labeler):
    p = Project.create(id=uuid4(), owner=admin, name="P1", description="d", labels={"a"})
    p.add_labeler(labeler.id)
    user_ctx, project_ctx, test_client = make_client(users=[admin, labeler], projects=[p])
    with user_ctx, project_ctx:
        response = test_client.get("/v1/projects")
    body = response.json()
    assert body["items"][0]["labeler_count"] == 1
    assert "labelers" not in body["items"][0]


# --- get project detail ---

def test_get_project_returns_200(client_with_project, project):
    response = client_with_project.get(f"/v1/projects/{project.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "My Project"
    assert body["description"] == "desc"
    assert "labelers" in body


def test_get_project_returns_resolved_labelers(admin, labeler):
    p = Project.create(id=uuid4(), owner=admin, name="P1", description="d", labels={"a"})
    p.add_labeler(labeler.id)
    user_ctx, project_ctx, test_client = make_client(users=[admin, labeler], projects=[p])
    with user_ctx, project_ctx:
        response = test_client.get(f"/v1/projects/{p.id}")
    body = response.json()
    assert len(body["labelers"]) == 1
    assert body["labelers"][0]["id"] == str(labeler.id)
    assert body["labelers"][0]["username"] == "labeler"


def test_get_project_returns_404_when_not_found(client):
    response = client.get(f"/v1/projects/{uuid4()}")
    assert response.status_code == 404


# --- update project ---

def test_update_project_name_returns_200(client_with_project, project):
    response = client_with_project.patch(f"/v1/projects/{project.id}", json={"name": "Updated"})
    assert response.status_code == 200
    assert response.json()["name"] == "Updated"
    assert response.json()["description"] == "desc"


def test_update_project_description_returns_200(client_with_project, project):
    response = client_with_project.patch(f"/v1/projects/{project.id}", json={"description": "New desc"})
    assert response.status_code == 200
    assert response.json()["description"] == "New desc"
    assert response.json()["name"] == "My Project"


def test_update_project_labelers_returns_200(client_with_project, project, labeler):
    response = client_with_project.patch(f"/v1/projects/{project.id}", json={
        "labeler_ids": [str(labeler.id)],
    })
    assert response.status_code == 200


def test_update_project_returns_404_when_project_not_found(client_with_project):
    response = client_with_project.patch(f"/v1/projects/{uuid4()}", json={"name": "x"})
    assert response.status_code == 404


def test_update_project_returns_404_when_labeler_not_found(client_with_project, project):
    response = client_with_project.patch(f"/v1/projects/{project.id}", json={
        "labeler_ids": [str(uuid4())],
    })
    assert response.status_code == 404


def test_update_project_returns_403_when_user_is_not_labeler(client_with_project, project, admin):
    response = client_with_project.patch(f"/v1/projects/{project.id}", json={
        "labeler_ids": [str(admin.id)],
    })
    assert response.status_code == 403


# --- list projects ---

def test_list_projects_returns_empty_list(client):
    response = client.get("/v1/projects")
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] == 0
    assert body["limit"] == 20
    assert body["offset"] == 0


def test_list_projects_returns_all_projects(admin):
    p1 = Project.create(id=uuid4(), owner=admin, name="P1", description="d1", labels={"a"})
    p2 = Project.create(id=uuid4(), owner=admin, name="P2", description="d2", labels={"b"})
    user_ctx, project_ctx, test_client = make_client(users=[admin], projects=[p1, p2])
    with user_ctx, project_ctx:
        response = test_client.get("/v1/projects")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2
    names = {item["name"] for item in body["items"]}
    assert names == {"P1", "P2"}


def test_list_projects_pagination(admin):
    projects = [
        Project.create(
            id=uuid4(), owner=admin, name=f"P{i}", description="d", labels={"a"},
            created_at=datetime(2024, 1, i + 1, tzinfo=timezone.utc),
        )
        for i in range(3)
    ]
    user_ctx, project_ctx, test_client = make_client(users=[admin], projects=projects)
    with user_ctx, project_ctx:
        response = test_client.get("/v1/projects", params={"limit": 2, "offset": 0})
        body = response.json()
        assert body["total"] == 3
        assert len(body["items"]) == 2
        assert body["items"][0]["name"] == "P2"
        assert body["items"][1]["name"] == "P1"

        response = test_client.get("/v1/projects", params={"limit": 2, "offset": 2})
        body = response.json()
        assert body["total"] == 3
        assert len(body["items"]) == 1
        assert body["items"][0]["name"] == "P0"


def test_list_projects_invalid_limit(client):
    response = client.get("/v1/projects", params={"limit": 0})
    assert response.status_code == 422

    response = client.get("/v1/projects", params={"limit": 200})
    assert response.status_code == 422


def test_list_projects_invalid_offset(client):
    response = client.get("/v1/projects", params={"offset": -1})
    assert response.status_code == 422


# --- filter by name ---

def test_list_projects_filter_by_name(admin):
    p1 = Project.create(id=uuid4(), owner=admin, name="Alpha Project", description="d", labels={"a"})
    p2 = Project.create(id=uuid4(), owner=admin, name="Beta Project", description="d", labels={"a"})
    p3 = Project.create(id=uuid4(), owner=admin, name="Gamma", description="d", labels={"a"})
    user_ctx, project_ctx, test_client = make_client(users=[admin], projects=[p1, p2, p3])
    with user_ctx, project_ctx:
        response = test_client.get("/v1/projects", params={"name": "alpha"})
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["name"] == "Alpha Project"


def test_list_projects_filter_by_name_case_insensitive(admin):
    p1 = Project.create(id=uuid4(), owner=admin, name="Alpha Project", description="d", labels={"a"})
    user_ctx, project_ctx, test_client = make_client(users=[admin], projects=[p1])
    with user_ctx, project_ctx:
        response = test_client.get("/v1/projects", params={"name": "ALPHA"})
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["name"] == "Alpha Project"


def test_list_projects_filter_by_name_contains(admin):
    p1 = Project.create(id=uuid4(), owner=admin, name="Alpha Project", description="d", labels={"a"})
    p2 = Project.create(id=uuid4(), owner=admin, name="Beta Project", description="d", labels={"a"})
    p3 = Project.create(id=uuid4(), owner=admin, name="Gamma", description="d", labels={"a"})
    user_ctx, project_ctx, test_client = make_client(users=[admin], projects=[p1, p2, p3])
    with user_ctx, project_ctx:
        response = test_client.get("/v1/projects", params={"name": "Project"})
    body = response.json()
    assert body["total"] == 2
    names = {item["name"] for item in body["items"]}
    assert names == {"Alpha Project", "Beta Project"}


def test_list_projects_filter_by_name_no_match(admin):
    p1 = Project.create(id=uuid4(), owner=admin, name="Alpha", description="d", labels={"a"})
    user_ctx, project_ctx, test_client = make_client(users=[admin], projects=[p1])
    with user_ctx, project_ctx:
        response = test_client.get("/v1/projects", params={"name": "nonexistent"})
    body = response.json()
    assert body["total"] == 0
    assert body["items"] == []


def test_list_projects_filter_by_name_with_pagination(admin):
    projects = [
        Project.create(
            id=uuid4(), owner=admin, name=f"Test {i}", description="d", labels={"a"},
            created_at=datetime(2024, 1, i + 1, tzinfo=timezone.utc),
        )
        for i in range(3)
    ]
    user_ctx, project_ctx, test_client = make_client(users=[admin], projects=projects)
    with user_ctx, project_ctx:
        response = test_client.get("/v1/projects", params={"name": "Test", "limit": 2})
    body = response.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2
