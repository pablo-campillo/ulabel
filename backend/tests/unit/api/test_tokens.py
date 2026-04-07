from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from tests.unit.conftest import make_uow
from ulabel.api.main import app
from ulabel.domain.users import User, UserRole
from ulabel.infrastructure.repositories.in_memory.user_repository import InMemoryUserRepository


@pytest.fixture
def labeler():
    return User.create_labeler(id=uuid4(), username="alice")


@pytest.fixture
def client(labeler):
    uow = make_uow(user_repository=InMemoryUserRepository(users=[labeler]))
    with app.container.unit_of_work.override(uow):
        yield TestClient(app)


def test_post_token_returns_claim(client, labeler):
    response = client.post("/v1/token", json={"username": "alice"})
    assert response.status_code == 200
    body = response.json()
    assert body["username"] == labeler.username
    assert body["id"] == str(labeler.id)


def test_post_token_returns_404_when_user_not_found(client):
    response = client.post("/v1/token", json={"username": "unknown"})
    assert response.status_code == 404


def test_post_token_claim_contains_correct_role(client, labeler):
    response = client.post("/v1/token", json={"username": "alice"})
    assert response.json()["role"] == UserRole.LABELER.value
