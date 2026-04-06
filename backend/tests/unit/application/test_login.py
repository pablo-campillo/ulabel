from uuid import uuid4

import pytest

from ulabel.application.login import LoginUseCase, UserNotFound
from ulabel.domain.users import User
from ulabel.infrastructure.repositories.in_memory.user_repository import InMemoryUserRepository


@pytest.fixture
def labeler():
    return User.create_labeler(id=uuid4(), username="alice")


@pytest.fixture
def use_case(labeler):
    return LoginUseCase(InMemoryUserRepository(users=[labeler]))


async def test_login_returns_user_when_username_exists(use_case, labeler):
    user = await use_case.execute("alice")
    assert user.id == labeler.id


async def test_login_raises_when_username_not_found(use_case):
    with pytest.raises(UserNotFound):
        await use_case.execute("unknown")
