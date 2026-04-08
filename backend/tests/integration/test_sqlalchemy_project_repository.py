from uuid import uuid4

import pytest

from ulabel.domain.projects import Project
from ulabel.domain.users import User
from ulabel.infrastructure.repositories.sql.project_repository import (
    SqlAlchemyProjectRepository,
)
from ulabel.infrastructure.repositories.sql.user_repository import SqlAlchemyUserRepository


@pytest.fixture
def user_repo(session):
    return SqlAlchemyUserRepository(session)


@pytest.fixture
def repo(session):
    return SqlAlchemyProjectRepository(session)


@pytest.fixture
async def admin(user_repo) -> User:
    admin = User.create_admin(id=uuid4(), username="admin")
    await user_repo.save(admin)
    return admin


@pytest.fixture
async def labeler(user_repo) -> User:
    labeler = User.create_labeler(id=uuid4(), username="labeler")
    await user_repo.save(labeler)
    return labeler


@pytest.fixture
async def saved_project(repo, admin) -> Project:
    project = Project.create(
        id=uuid4(), owner=admin, name="Test Project", description="desc", labels={"cat", "dog"}
    )
    await repo.save(project)
    return project


async def test_get_by_id_returns_project(repo, saved_project):
    found = await repo.get_by_id(saved_project.id)
    assert found.id == saved_project.id
    assert found.name == "Test Project"
    assert found.labels == {"cat", "dog"}


async def test_get_by_id_returns_none_when_not_found(repo):
    assert await repo.get_by_id(uuid4()) is None


async def test_save_updates_existing_project(repo, saved_project):
    saved_project.name = "Updated Name"
    await repo.save(saved_project)
    found = await repo.get_by_id(saved_project.id)
    assert found.name == "Updated Name"


async def test_save_updates_labels(repo, saved_project):
    saved_project.labels = {"new_label"}
    await repo.save(saved_project)
    found = await repo.get_by_id(saved_project.id)
    assert found.labels == {"new_label"}


async def test_add_labeler_and_query_by_labeler(repo, saved_project, labeler):
    saved_project.add_labeler(labeler.id)
    await repo.save(saved_project)

    projects = await repo.get_by_labeler_id(labeler.id)
    assert any(p.id == saved_project.id for p in projects)


async def test_get_by_labeler_id_returns_empty_when_no_projects(repo, labeler):
    projects = await repo.get_by_labeler_id(labeler.id)
    assert projects == []


async def test_save_multiple_labelers(repo, user_repo, saved_project):
    """Saving a project with multiple labelers persists all of them."""
    labeler_ids = set()
    for i in range(5):
        labeler = User.create_labeler(id=uuid4(), username=f"labeler_{i}")
        await user_repo.save(labeler)
        labeler_ids.add(labeler.id)

    saved_project.set_labelers(labeler_ids)
    await repo.save(saved_project)

    found = await repo.get_by_id(saved_project.id)
    assert found.labeler_ids == labeler_ids
