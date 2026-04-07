from uuid import uuid4

import pytest

from ulabel.application.add_labeler_to_project import ProjectNotFound
from ulabel.application.create_project import Unauthorized
from ulabel.application.login import UserNotFound
from ulabel.application.update_project import UpdateProjectUseCase
from ulabel.domain.projects import Project
from ulabel.domain.users import User
from ulabel.infrastructure.repositories.in_memory.project_repository import (
    InMemoryProjectRepository,
)
from ulabel.infrastructure.repositories.in_memory.user_repository import InMemoryUserRepository


@pytest.fixture
def labeler2():
    return User.create_labeler(id=uuid4(), username="labeler2")


@pytest.fixture
def project(admin):
    return Project.create(
        id=uuid4(),
        owner=admin,
        name="Original",
        description="Original desc",
        labels={"cat"},
    )


@pytest.fixture
def use_case(admin, labeler, labeler2, project):
    return UpdateProjectUseCase(
        user_repository=InMemoryUserRepository(users=[admin, labeler, labeler2]),
        project_repository=InMemoryProjectRepository(projects=[project]),
    )


async def test_update_name(use_case, project):
    result = await use_case.execute(project_id=project.id, name="New name")
    assert result.name == "New name"
    assert result.description == "Original desc"


async def test_update_description(use_case, project):
    result = await use_case.execute(project_id=project.id, description="New desc")
    assert result.description == "New desc"
    assert result.name == "Original"


async def test_update_name_and_description(use_case, project):
    result = await use_case.execute(project_id=project.id, name="N", description="D")
    assert result.name == "N"
    assert result.description == "D"


async def test_update_labelers(use_case, project, labeler, labeler2):
    result = await use_case.execute(project_id=project.id, labeler_ids={labeler.id, labeler2.id})
    assert result.labeler_ids == {labeler.id, labeler2.id}


async def test_update_labelers_replaces_existing(use_case, project, labeler, labeler2):
    await use_case.execute(project_id=project.id, labeler_ids={labeler.id, labeler2.id})
    result = await use_case.execute(project_id=project.id, labeler_ids={labeler.id})
    assert result.labeler_ids == {labeler.id}


async def test_update_labelers_to_empty_set(use_case, project, labeler):
    await use_case.execute(project_id=project.id, labeler_ids={labeler.id})
    result = await use_case.execute(project_id=project.id, labeler_ids=set())
    assert result.labeler_ids == set()


async def test_omitting_labeler_ids_preserves_existing(use_case, project, labeler):
    await use_case.execute(project_id=project.id, labeler_ids={labeler.id})
    result = await use_case.execute(project_id=project.id, name="New name")
    assert result.labeler_ids == {labeler.id}


async def test_raises_when_project_not_found(use_case):
    with pytest.raises(ProjectNotFound):
        await use_case.execute(project_id=uuid4(), name="x")


async def test_raises_when_labeler_not_found(use_case, project):
    with pytest.raises(UserNotFound):
        await use_case.execute(project_id=project.id, labeler_ids={uuid4()})


async def test_raises_when_user_is_not_labeler(use_case, project, admin):
    with pytest.raises(Unauthorized):
        await use_case.execute(project_id=project.id, labeler_ids={admin.id})
