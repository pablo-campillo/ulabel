from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from tests.unit.conftest import make_uow
from ulabel.api.main import app
from ulabel.domain.errors import StorageFull
from ulabel.domain.labels import LabelRecord
from ulabel.domain.projects import Project
from ulabel.infrastructure.repositories.in_memory.label_repository import InMemoryLabelRepository
from ulabel.infrastructure.repositories.in_memory.project_repository import (
    InMemoryProjectRepository,
)
from ulabel.infrastructure.storage.fake_storage_service import FakeStorageService


@pytest.fixture
def project(admin):
    return Project.create(
        id=uuid4(), owner=admin, name="TestProject", description="desc", labels={"cat", "dog"}
    )


@pytest.fixture
def label_records(project):
    labeler_id = uuid4()
    return [
        LabelRecord.create(
            id=uuid4(),
            project_id=project.id,
            image_id=uuid4(),
            labeler_id=labeler_id,
            label="cat",
        ),
        LabelRecord.create(
            id=uuid4(),
            project_id=project.id,
            image_id=uuid4(),
            labeler_id=labeler_id,
            label="dog",
        ),
    ]


@pytest.fixture
def label_repo(label_records):
    repo = InMemoryLabelRepository()
    for rec in label_records:
        repo._records[rec.id] = rec
    return repo


@pytest.fixture
def storage():
    return FakeStorageService()


@pytest.fixture
def client(project, label_repo, storage):
    uow = make_uow(
        project_repository=InMemoryProjectRepository(projects=[project]),
        label_repository=label_repo,
    )
    with (
        app.container.unit_of_work.override(uow),
        app.container.storage_service.override(storage),
    ):
        yield TestClient(app, follow_redirects=False)


def test_export_json_returns_307(client, project):
    response = client.get(f"/v1/projects/{project.id}/export?format=json")
    assert response.status_code == 307
    assert "fake-storage" in response.headers["location"]


def test_export_csv_returns_307(client, project):
    response = client.get(f"/v1/projects/{project.id}/export?format=csv")
    assert response.status_code == 307
    assert "fake-storage" in response.headers["location"]


def test_export_returns_404_when_project_not_found(client):
    response = client.get(f"/v1/projects/{uuid4()}/export?format=json")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PROJECT_NOT_FOUND"


def test_export_returns_404_when_no_labels(project, storage):
    uow = make_uow(
        project_repository=InMemoryProjectRepository(projects=[project]),
        label_repository=InMemoryLabelRepository(),
    )
    with (
        app.container.unit_of_work.override(uow),
        app.container.storage_service.override(storage),
    ):
        client = TestClient(app, follow_redirects=False)
        response = client.get(f"/v1/projects/{project.id}/export?format=json")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NO_LABELS_FOUND"


class FullStorageService(FakeStorageService):
    """Fake that raises StorageFull on streaming upload."""

    async def upload_file_streaming(
        self,
        key: str,
        chunks: AsyncIterator[bytes],
        content_type: str,
        metadata: dict[str, str] | None = None,
    ) -> None:
        raise StorageFull("Storage backend has reached its minimum free drive threshold.")


def test_export_returns_507_when_storage_full(project, label_repo):
    uow = make_uow(
        project_repository=InMemoryProjectRepository(projects=[project]),
        label_repository=label_repo,
    )
    with (
        app.container.unit_of_work.override(uow),
        app.container.storage_service.override(FullStorageService()),
    ):
        client = TestClient(app, follow_redirects=False)
        response = client.get(f"/v1/projects/{project.id}/export?format=json")
    assert response.status_code == 507
    assert response.json()["error"]["code"] == "STORAGE_FULL"
