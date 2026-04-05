from uuid import uuid4

import pytest

from ulabel.application.create_project import CreateProjectUseCase, Unauthorized
from ulabel.application.login import UserNotFound
from ulabel.infrastructure.repositories.in_memory_project_repository import (
    InMemoryProjectRepository,
)
from ulabel.infrastructure.repositories.in_memory_user_repository import InMemoryUserRepository


@pytest.fixture
def use_case(admin, labeler):
    return CreateProjectUseCase(
        user_repository=InMemoryUserRepository(users=[admin, labeler]),
        project_repository=InMemoryProjectRepository(),
    )


async def test_create_project_returns_project(use_case, admin):
    project = await use_case.execute(
        owner_id=admin.id,
        name="My Project",
        description="A test project",
        labels={"cat", "dog"},
    )
    assert project.name == "My Project"
    assert project.owner.id == admin.id
    assert project.labels == {"cat", "dog"}


async def test_create_project_raises_when_owner_not_found(use_case):
    with pytest.raises(UserNotFound):
        await use_case.execute(owner_id=uuid4(), name="x", description="x", labels=set())


async def test_create_project_raises_when_owner_is_not_admin(use_case, labeler):
    with pytest.raises(Unauthorized):
        await use_case.execute(owner_id=labeler.id, name="x", description="x", labels=set())
