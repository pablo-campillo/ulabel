from uuid import uuid4

import pytest

from ulabel.application.create_project import Unauthorized
from ulabel.application.get_labeler_projects import GetLabelerProjectsUseCase
from ulabel.application.login import UserNotFound
from ulabel.domain.projects import Project
from ulabel.domain.users import User
from ulabel.infrastructure.repositories.in_memory.project_repository import (
    InMemoryProjectRepository,
)
from ulabel.infrastructure.repositories.in_memory.user_repository import InMemoryUserRepository


@pytest.fixture
def other_labeler():
    return User.create_labeler(id=uuid4(), username="other_labeler")


@pytest.fixture
def project_with_labeler(admin, labeler):
    p = Project.create(
        id=uuid4(),
        owner=admin,
        name="Project A",
        description="desc",
        labels={"cat"},
    )
    p.add_labeler(labeler.id)
    return p


@pytest.fixture
def project_without_labeler(admin):
    return Project.create(
        id=uuid4(),
        owner=admin,
        name="Project B",
        description="desc",
        labels={"dog"},
    )


@pytest.fixture
def use_case(admin, labeler, other_labeler, project_with_labeler, project_without_labeler):
    return GetLabelerProjectsUseCase(
        user_repository=InMemoryUserRepository(users=[admin, labeler, other_labeler]),
        project_repository=InMemoryProjectRepository(
            projects=[project_with_labeler, project_without_labeler]
        ),
    )


async def test_returns_projects_for_labeler(use_case, labeler, project_with_labeler):
    result = await use_case.execute(labeler_id=labeler.id)
    assert project_with_labeler in result


async def test_does_not_return_projects_labeler_is_not_in(
    use_case,
    labeler,
    project_without_labeler,
):
    result = await use_case.execute(labeler_id=labeler.id)
    assert project_without_labeler not in result


async def test_returns_empty_list_when_labeler_has_no_projects(use_case, other_labeler):
    result = await use_case.execute(labeler_id=other_labeler.id)
    assert result == []


async def test_raises_when_user_not_found(use_case):
    with pytest.raises(UserNotFound):
        await use_case.execute(labeler_id=uuid4())


async def test_raises_when_user_is_not_labeler(use_case, admin):
    with pytest.raises(Unauthorized):
        await use_case.execute(labeler_id=admin.id)
