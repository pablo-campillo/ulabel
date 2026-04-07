from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from tests.unit.conftest import make_uow
from ulabel.api.main import app
from ulabel.domain.projects import Project
from ulabel.domain.users import User
from ulabel.infrastructure.repositories.in_memory.project_repository import (
    InMemoryProjectRepository,
)
from ulabel.infrastructure.repositories.in_memory.user_repository import InMemoryUserRepository


@pytest.fixture
def project(admin, labeler):
    p = Project.create(
        id=uuid4(),
        owner=admin,
        name="Project A",
        description="desc",
        labels={"cat"},
    )
    p.add_labeler(labeler.id)
    return p


@pytest.fixture
def client(admin, labeler, project):
    uow = make_uow(
        user_repository=InMemoryUserRepository(users=[admin, labeler]),
        project_repository=InMemoryProjectRepository(projects=[project]),
    )
    with app.container.unit_of_work.override(uow):
        yield TestClient(app)


def test_get_labeler_projects_returns_200(client, labeler, project):
    response = client.get(f"/v1/labelers/{labeler.id}/projects")
    assert response.status_code == 200
    ids = [p["id"] for p in response.json()]
    assert str(project.id) in ids


def test_get_labeler_projects_returns_empty_list(client, admin, labeler):
    other_labeler = User.create_labeler(id=uuid4(), username="other")
    uow = make_uow(
        user_repository=InMemoryUserRepository(users=[admin, labeler, other_labeler]),
        project_repository=InMemoryProjectRepository(projects=[]),
    )
    with app.container.unit_of_work.override(uow):
        response = TestClient(app).get(f"/v1/labelers/{other_labeler.id}/projects")
    assert response.status_code == 200
    assert response.json() == []


def test_get_labeler_projects_returns_404_when_labeler_not_found(client):
    response = client.get(f"/v1/labelers/{uuid4()}/projects")
    assert response.status_code == 404


def test_get_labeler_projects_returns_403_when_user_is_not_labeler(client, admin):
    response = client.get(f"/v1/labelers/{admin.id}/projects")
    assert response.status_code == 403
