from uuid import uuid4

import pytest

from tests.unit.conftest import make_uow
from ulabel.application.add_labeler_to_project import AddLabelerToProjectUseCase, ProjectNotFound
from ulabel.application.create_project import Unauthorized
from ulabel.application.login import UserNotFound
from ulabel.domain.projects import Project
from ulabel.infrastructure.repositories.in_memory.project_repository import (
    InMemoryProjectRepository,
)
from ulabel.infrastructure.repositories.in_memory.user_repository import InMemoryUserRepository


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
def use_case(admin, labeler, project):
    return AddLabelerToProjectUseCase(
        uow=make_uow(
            user_repository=InMemoryUserRepository(users=[admin, labeler]),
            project_repository=InMemoryProjectRepository(projects=[project]),
        ),
    )


async def test_add_labeler_adds_labeler_to_project(use_case, project, labeler):
    result = await use_case.execute(project_id=project.id, labeler_id=labeler.id)
    assert labeler.id in result.labeler_ids


async def test_add_labeler_is_idempotent(use_case, project, labeler):
    await use_case.execute(project_id=project.id, labeler_id=labeler.id)
    result = await use_case.execute(project_id=project.id, labeler_id=labeler.id)
    assert len([x for x in result.labeler_ids if x == labeler.id]) == 1


async def test_add_labeler_raises_when_project_not_found(use_case, labeler):
    with pytest.raises(ProjectNotFound):
        await use_case.execute(project_id=uuid4(), labeler_id=labeler.id)


async def test_add_labeler_raises_when_user_not_found(use_case, project):
    with pytest.raises(UserNotFound):
        await use_case.execute(project_id=project.id, labeler_id=uuid4())


async def test_add_labeler_raises_when_user_is_not_labeler(use_case, project, admin):
    with pytest.raises(Unauthorized):
        await use_case.execute(project_id=project.id, labeler_id=admin.id)
