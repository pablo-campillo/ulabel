from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from ulabel.api.main import app
from ulabel.domain.images import Image, ImageStatus
from ulabel.domain.labels import LabelRecord
from ulabel.domain.projects import Project
from ulabel.domain.users import User
from ulabel.infrastructure.repositories.in_memory_project_repository import (
    InMemoryProjectRepository,
)
from ulabel.infrastructure.repositories.in_memory_stats_repository import InMemoryStatsRepository


@pytest.fixture
def admin():
    return User.create_admin(id=uuid4(), username="admin")


@pytest.fixture
def labeler():
    return User.create_labeler(id=uuid4(), username="ana")


@pytest.fixture
def project(admin, labeler):
    p = Project.create(
        id=uuid4(), owner=admin, name="Proj", description="d", labels={"cat", "dog"}
    )
    p.add_labeler(labeler.id)
    return p


@pytest.fixture
def images_and_labels(project, labeler):
    images = [
        Image.create(id=uuid4(), project_id=project.id, storage_key="a.jpg"),
        Image.create(id=uuid4(), project_id=project.id, storage_key="b.jpg"),
    ]
    images[0].status = ImageStatus.DONE
    labels = [
        LabelRecord.create(
            id=uuid4(), project_id=project.id, image_id=images[0].id,
            labeler_id=labeler.id, label="cat",
        )
    ]
    return images, labels


@pytest.fixture
def client(project, images_and_labels, labeler):
    images, labels = images_and_labels
    usernames = {labeler.id: labeler.username}
    with (
        app.container.project_repository.override(
            InMemoryProjectRepository(projects=[project])
        ),
        app.container.stats_repository.override(
            InMemoryStatsRepository(images=images, labels=labels, usernames=usernames)
        ),
    ):
        yield TestClient(app)


def test_get_stats_returns_200(client, project):
    response = client.get(f"/v1/projects/{project.id}/stats")
    assert response.status_code == 200
    body = response.json()
    assert body["total_images"] == 2
    assert body["labeled_images"] == 1
    assert body["class_distribution"] == {"cat": 1}
    assert len(body["labeler_class_counts"]) == 1
    assert body["labeler_class_counts"][0]["counts"] == {"cat": 1}


def test_get_stats_returns_404_for_unknown_project(client):
    response = client.get(f"/v1/projects/{uuid4()}/stats")
    assert response.status_code == 404
