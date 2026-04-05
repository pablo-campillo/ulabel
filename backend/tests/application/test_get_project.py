from uuid import uuid4

import pytest

from ulabel.application.add_labeler_to_project import ProjectNotFound
from ulabel.application.get_project import GetProjectUseCase
from ulabel.domain.projects import Project
from ulabel.domain.users import User
from ulabel.infrastructure.repositories.in_memory_project_repository import (
    InMemoryProjectRepository,
)
from ulabel.infrastructure.repositories.in_memory_user_repository import InMemoryUserRepository


@pytest.fixture
def admin():
    return User.create_admin(id=uuid4(), username="admin")


@pytest.fixture
def labeler():
    return User.create_labeler(id=uuid4(), username="labeler1")


@pytest.fixture
def labeler2():
    return User.create_labeler(id=uuid4(), username="labeler2")


@pytest.fixture
def project(admin, labeler, labeler2):
    p = Project.create(id=uuid4(), owner=admin, name="Test", description="d", labels={"a"})
    p.add_labeler(labeler.id)
    p.add_labeler(labeler2.id)
    return p


@pytest.fixture
def use_case(admin, labeler, labeler2, project):
    return GetProjectUseCase(
        project_repository=InMemoryProjectRepository(projects=[project]),
        user_repository=InMemoryUserRepository(users=[admin, labeler, labeler2]),
    )


async def test_returns_project_with_resolved_labelers(use_case, project, labeler, labeler2):
    result = await use_case.execute(project_id=project.id)
    assert result.project.id == project.id
    assert len(result.labelers) == 2
    usernames = {lab.username for lab in result.labelers}
    assert usernames == {"labeler1", "labeler2"}


async def test_raises_when_project_not_found(use_case):
    with pytest.raises(ProjectNotFound):
        await use_case.execute(project_id=uuid4())


async def test_handles_missing_labeler_user(admin, labeler):
    p = Project.create(id=uuid4(), owner=admin, name="Test", description="d", labels={"a"})
    missing_id = uuid4()
    p.add_labeler(labeler.id)
    p.add_labeler(missing_id)
    use_case = GetProjectUseCase(
        project_repository=InMemoryProjectRepository(projects=[p]),
        user_repository=InMemoryUserRepository(users=[admin, labeler]),
    )
    result = await use_case.execute(project_id=p.id)
    assert len(result.labelers) == 2
    usernames = {lab.username for lab in result.labelers}
    assert labeler.username in usernames
    assert str(missing_id) in usernames
