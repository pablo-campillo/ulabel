from uuid import uuid4

import pytest

from ulabel.domain.users import User
from ulabel.infrastructure.repositories.sqlalchemy_user_repository import SqlAlchemyUserRepository


@pytest.fixture
def repo(sessionmaker):
    return SqlAlchemyUserRepository(sessionmaker)


@pytest.fixture
async def saved_admin(repo) -> User:
    admin = User.create_admin(id=uuid4(), username="admin")
    await repo.save(admin)
    return admin


async def test_get_by_username_returns_user(repo, saved_admin):
    user = await repo.get_by_username("admin")
    assert user.id == saved_admin.id
    assert user.username == "admin"


async def test_get_by_username_returns_none_when_not_found(repo):
    assert await repo.get_by_username("unknown") is None


async def test_get_by_id_returns_user(repo, saved_admin):
    user = await repo.get_by_id(saved_admin.id)
    assert user.id == saved_admin.id


async def test_get_by_id_returns_none_when_not_found(repo):
    assert await repo.get_by_id(uuid4()) is None


async def test_save_preserves_role(repo):
    labeler = User.create_labeler(id=uuid4(), username="labeler")
    await repo.save(labeler)
    found = await repo.get_by_id(labeler.id)
    assert found.role == labeler.role
