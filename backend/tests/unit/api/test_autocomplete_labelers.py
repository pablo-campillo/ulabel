from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from ulabel.api.main import app
from ulabel.domain.users import User
from ulabel.infrastructure.repositories.in_memory.user_repository import InMemoryUserRepository


@pytest.fixture
def labelers():
    return [
        User.create_labeler(id=uuid4(), username="alice"),
        User.create_labeler(id=uuid4(), username="alicia"),
        User.create_labeler(id=uuid4(), username="bob"),
    ]


@pytest.fixture
def admin():
    return User.create_admin(id=uuid4(), username="alvaro")


@pytest.fixture
def client(labelers, admin):
    repo = InMemoryUserRepository(users=[*labelers, admin])
    with app.container.user_repository.override(repo):
        yield TestClient(app)


def test_autocomplete_returns_matching_labelers(client):
    response = client.get("/v1/labelers/autocomplete", params={"q": "ali"})
    assert response.status_code == 200
    usernames = [item["username"] for item in response.json()]
    assert usernames == ["alice", "alicia"]


def test_autocomplete_excludes_admins(client):
    response = client.get("/v1/labelers/autocomplete", params={"q": "al"})
    assert response.status_code == 200
    usernames = [item["username"] for item in response.json()]
    assert "alvaro" not in usernames


def test_autocomplete_returns_empty_list_when_no_match(client):
    response = client.get("/v1/labelers/autocomplete", params={"q": "zzz"})
    assert response.status_code == 200
    assert response.json() == []


def test_autocomplete_respects_limit(client):
    response = client.get("/v1/labelers/autocomplete", params={"q": "al", "limit": 1})
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_autocomplete_returns_id_and_username(client, labelers):
    response = client.get("/v1/labelers/autocomplete", params={"q": "bob"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["username"] == "bob"
    assert body[0]["id"] == str(labelers[2].id)


def test_autocomplete_returns_422_when_q_is_empty(client):
    response = client.get("/v1/labelers/autocomplete", params={"q": ""})
    assert response.status_code == 422


def test_autocomplete_returns_422_when_q_is_missing(client):
    response = client.get("/v1/labelers/autocomplete")
    assert response.status_code == 422
