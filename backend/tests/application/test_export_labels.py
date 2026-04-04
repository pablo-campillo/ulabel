import json

import pytest
from uuid import uuid4

from ulabel.application.add_labeler_to_project import ProjectNotFound
from ulabel.application.export_labels import ExportFormat, ExportLabelsUseCase, NoLabelsFound
from ulabel.domain.labels import LabelRecord
from ulabel.domain.users import User
from ulabel.infrastructure.repositories.in_memory_label_repository import InMemoryLabelRepository
from ulabel.infrastructure.repositories.in_memory_project_repository import InMemoryProjectRepository
from ulabel.infrastructure.storage.fake_storage_service import FakeStorageService


@pytest.fixture
def admin():
    return User.create_admin(id=uuid4(), username="admin")


@pytest.fixture
def project(admin):
    from ulabel.domain.projects import Project

    return Project.create(
        id=uuid4(),
        owner=admin,
        name="Test Project",
        description="desc",
        labels={"cat", "dog"},
    )


@pytest.fixture
def label_records(project):
    image_ids = [uuid4(), uuid4(), uuid4()]
    labeler_id = uuid4()
    return [
        LabelRecord.create(id=uuid4(), project_id=project.id, image_id=img_id, labeler_id=labeler_id, label=label)
        for img_id, label in zip(image_ids, ["cat", "dog", "cat"])
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
def use_case(project, label_repo, storage):
    return ExportLabelsUseCase(
        project_repository=InMemoryProjectRepository(projects=[project]),
        label_repository=label_repo,
        storage_service=storage,
    )


async def test_export_csv(use_case, project, storage, label_records):
    result = await use_case.execute(project.id, ExportFormat.CSV)

    assert result.cache_hit is False
    assert "fake-storage" in result.url

    key = f"exports/{project.id}/{project.id}.csv"
    data = storage._uploaded[key]["data"].decode("utf-8")
    lines = data.strip().splitlines()
    assert lines[0] == "image_id,storage_key,value"
    assert len(lines) == 1 + len(label_records)


async def test_export_json(use_case, project, storage, label_records):
    result = await use_case.execute(project.id, ExportFormat.JSON)

    assert result.cache_hit is False

    key = f"exports/{project.id}/{project.id}.json"
    data = storage._uploaded[key]["data"].decode("utf-8")
    parsed = json.loads(data)
    assert isinstance(parsed, list)
    assert len(parsed) == len(label_records)
    assert all("image_id" in entry and "storage_key" in entry and "value" in entry for entry in parsed)


async def test_export_cache_hit(use_case, project, storage, label_records):
    await use_case.execute(project.id, ExportFormat.JSON)
    result = await use_case.execute(project.id, ExportFormat.JSON)
    assert result.cache_hit is True


async def test_export_no_labels(project, storage):
    use_case = ExportLabelsUseCase(
        project_repository=InMemoryProjectRepository(projects=[project]),
        label_repository=InMemoryLabelRepository(),
        storage_service=storage,
    )
    with pytest.raises(NoLabelsFound):
        await use_case.execute(project.id, ExportFormat.CSV)


async def test_export_project_not_found(label_repo, storage):
    use_case = ExportLabelsUseCase(
        project_repository=InMemoryProjectRepository(),
        label_repository=label_repo,
        storage_service=storage,
    )
    with pytest.raises(ProjectNotFound):
        await use_case.execute(uuid4(), ExportFormat.CSV)


async def test_export_metadata_stores_label_count(use_case, project, storage, label_records):
    await use_case.execute(project.id, ExportFormat.CSV)

    key = f"exports/{project.id}/{project.id}.csv"
    metadata = storage._uploaded[key]["metadata"]
    assert metadata["label_count"] == str(len(label_records))
