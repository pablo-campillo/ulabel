import pytest
from datetime import datetime, timezone
from uuid import uuid4
from fastapi.testclient import TestClient

from ulabel.api.main import app
from ulabel.domain.images import Image
from ulabel.domain.projects import Project
from ulabel.domain.users import User
from ulabel.infrastructure.repositories.in_memory_image_repository import InMemoryImageRepository
from ulabel.infrastructure.repositories.in_memory_label_repository import InMemoryLabelRepository
from ulabel.infrastructure.repositories.in_memory_project_repository import InMemoryProjectRepository
from ulabel.infrastructure.repositories.in_memory_stats_repository import InMemoryStatsRepository

FIXED_NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def admin():
    return User.create_admin(id=uuid4(), username="admin")


@pytest.fixture
def labeler():
    return User.create_labeler(id=uuid4(), username="labeler")


@pytest.fixture
def project(admin, labeler):
    p = Project.create(
        id=uuid4(), owner=admin, name="Project", description="desc", labels={"cat", "dog"}
    )
    p.add_labeler(labeler.id)
    return p


@pytest.fixture
def assigned_image(project, labeler):
    img = Image.create(id=uuid4(), project_id=project.id, storage_key="img.jpg")
    img.assign(labeler_id=labeler.id, assigned_at=FIXED_NOW)
    return img


@pytest.fixture
def client(project, assigned_image, labeler):
    images = [assigned_image]
    labels = []
    with (
        app.container.project_repository.override(
            InMemoryProjectRepository(projects=[project])
        ),
        app.container.image_repository.override(
            InMemoryImageRepository(images=images)
        ),
        app.container.label_repository.override(InMemoryLabelRepository()),
        app.container.stats_repository.override(
            InMemoryStatsRepository(images=images, labels=labels, usernames={labeler.id: labeler.username})
        ),
    ):
        yield TestClient(app)


def _url(project_id, image_id):
    return f"/v1/projects/{project_id}/images/{image_id}/label"


def _payload(labeler_id, assignment_id, label="cat"):
    return {
        "labeler_id": str(labeler_id),
        "assignment_id": str(assignment_id),
        "label": label,
    }


def test_submit_label_returns_201(client, project, assigned_image, labeler):
    response = client.post(
        _url(project.id, assigned_image.id),
        json=_payload(labeler.id, assigned_image.assignment_id),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["project_id"] == str(project.id)
    assert body["image_id"] == str(assigned_image.id)
    assert body["labeler_id"] == str(labeler.id)
    assert body["label"] == "cat"
    assert "labeler_count" in body
    assert "ranking" in body
    assert "total_labelers" in body


def test_submit_label_returns_404_when_project_not_found(client, assigned_image, labeler):
    response = client.post(
        _url(uuid4(), assigned_image.id),
        json=_payload(labeler.id, assigned_image.assignment_id),
    )
    assert response.status_code == 404


def test_submit_label_returns_404_when_image_not_found(client, project, labeler, assigned_image):
    response = client.post(
        _url(project.id, uuid4()),
        json=_payload(labeler.id, assigned_image.assignment_id),
    )
    assert response.status_code == 404


def test_submit_label_returns_409_when_image_not_in_progress(project, labeler):
    pending_image = Image.create(id=uuid4(), project_id=project.id, storage_key="img2.jpg")
    with (
        app.container.project_repository.override(
            InMemoryProjectRepository(projects=[project])
        ),
        app.container.image_repository.override(
            InMemoryImageRepository(images=[pending_image])
        ),
        app.container.label_repository.override(InMemoryLabelRepository()),
        app.container.stats_repository.override(
            InMemoryStatsRepository(images=[pending_image], labels=[], usernames={})
        ),
    ):
        response = TestClient(app).post(
            _url(project.id, pending_image.id),
            json=_payload(labeler.id, uuid4()),
        )
    assert response.status_code == 409


def test_submit_label_returns_409_when_assignment_id_mismatch(
    client, project, assigned_image, labeler
):
    response = client.post(
        _url(project.id, assigned_image.id),
        json=_payload(labeler.id, uuid4()),
    )
    assert response.status_code == 409


def test_submit_label_returns_403_when_labeler_mismatch(client, project, assigned_image):
    response = client.post(
        _url(project.id, assigned_image.id),
        json=_payload(uuid4(), assigned_image.assignment_id),
    )
    assert response.status_code == 403


def test_submit_label_returns_422_when_invalid_label(
    client, project, assigned_image, labeler
):
    response = client.post(
        _url(project.id, assigned_image.id),
        json=_payload(labeler.id, assigned_image.assignment_id, label="airplane"),
    )
    assert response.status_code == 422
