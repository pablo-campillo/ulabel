from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from tests.unit.conftest import make_uow
from ulabel.api.main import app
from ulabel.domain.projects import Project
from ulabel.infrastructure.repositories.in_memory.image_repository import InMemoryImageRepository
from ulabel.infrastructure.repositories.in_memory.import_job_repository import (
    InMemoryImportJobRepository,
)
from ulabel.infrastructure.repositories.in_memory.project_repository import (
    InMemoryProjectRepository,
)
from ulabel.infrastructure.storage.fake_storage_service import FakeStorageService

STORAGE_OBJECTS = [
    "dataset/train/img001.jpg",
    "dataset/train/img002.jpg",
    "dataset/train/img003.jpg",
    "dataset/val/img004.jpg",
]


@pytest.fixture
def project(admin):
    return Project.create(
        id=uuid4(),
        owner=admin,
        name="My Project",
        description="desc",
        labels={"cat"},
    )


@pytest.fixture
def image_repo():
    return InMemoryImageRepository()


@pytest.fixture
def import_job_repo():
    return InMemoryImportJobRepository()


@pytest.fixture
def client(project, image_repo, import_job_repo):
    uow = make_uow(
        project_repository=InMemoryProjectRepository(projects=[project]),
        image_repository=image_repo,
        import_job_repository=import_job_repo,
    )
    with (
        app.container.unit_of_work.override(uow),
        app.container.storage_service.override(FakeStorageService(objects=STORAGE_OBJECTS)),
    ):
        yield TestClient(app)


def _import(client, project, prefix: str) -> dict:
    resp = client.post(f"/v1/projects/{project.id}/images/import", json={"prefix": prefix})
    assert resp.status_code == 202
    return resp.json()


def _get_status(client, project, import_id: str) -> dict:
    resp = client.get(f"/v1/projects/{project.id}/images/imports/{import_id}")
    assert resp.status_code == 200
    return resp.json()


def test_import_returns_202_with_job_info(client, project):
    body = _import(client, project, "dataset/train/")
    assert body["project_id"] == str(project.id)
    assert body["prefix"] == "dataset/train/"
    assert "import_id" in body


def test_import_runs_in_background_and_completes(client, project):
    # TestClient runs background tasks synchronously before returning
    job = _import(client, project, "dataset/train/")
    status = _get_status(client, project, job["import_id"])
    assert status["status"] == "done"
    assert status["imported"] == 3  # only 3 objects match "dataset/train/"


def test_import_full_prefix_imports_all_objects(client, project):
    job = _import(client, project, "dataset/")
    status = _get_status(client, project, job["import_id"])
    assert status["imported"] == 4


def test_import_returns_404_when_project_not_found(client):
    response = client.post(f"/v1/projects/{uuid4()}/images/import", json={"prefix": "dataset/"})
    assert response.status_code == 404


def test_get_import_status_returns_404_for_unknown_job(client, project):
    response = client.get(f"/v1/projects/{project.id}/images/imports/{uuid4()}")
    assert response.status_code == 404


def test_import_idempotent_does_not_create_duplicates(client, project, image_repo):
    _import(client, project, "dataset/train/")
    _import(client, project, "dataset/train/")
    # All 3 images should exist exactly once
    images = list(image_repo._images.values())
    keys = [img.storage_key for img in images if img.project_id == project.id]
    assert len(keys) == 3
    assert len(set(keys)) == 3


def test_import_job_persisted_in_repository(client, project, import_job_repo):
    job = _import(client, project, "dataset/train/")
    job_id = __import__("uuid").UUID(job["import_id"])
    assert job_id in import_job_repo._jobs
    persisted = import_job_repo._jobs[job_id]
    assert persisted.status.value == "done"
    assert persisted.imported == 3
