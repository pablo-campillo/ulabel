from uuid import uuid4

import pytest

from ulabel.domain.users import User
from ulabel.infrastructure.repositories.sqlalchemy_user_repository import SqlAlchemyUserRepository


@pytest.fixture
def repo(sessionmaker):
    return SqlAlchemyUserRepository(sessionmaker)


async def test_search_by_username_prefix_returns_matches(repo):
    alice = User.create_labeler(id=uuid4(), username="alice")
    alicia = User.create_labeler(id=uuid4(), username="alicia")
    bob = User.create_labeler(id=uuid4(), username="bob")
    for u in [alice, alicia, bob]:
        await repo.save(u)

    results = await repo.search_by_username_prefix("ali", role="labeler", limit=10)
    usernames = [u.username for u in results]
    assert usernames == ["alice", "alicia"]


async def test_search_by_username_prefix_is_case_insensitive(repo):
    alice = User.create_labeler(id=uuid4(), username="Alice")
    await repo.save(alice)

    results = await repo.search_by_username_prefix("ali", role="labeler", limit=10)
    assert len(results) == 1
    assert results[0].username == "Alice"


async def test_search_by_username_prefix_filters_by_role(repo):
    labeler = User.create_labeler(id=uuid4(), username="alvaro_lab")
    admin = User.create_admin(id=uuid4(), username="alvaro_adm")
    await repo.save(labeler)
    await repo.save(admin)

    results = await repo.search_by_username_prefix("alvaro", role="labeler", limit=10)
    usernames = [u.username for u in results]
    assert "alvaro_lab" in usernames
    assert "alvaro_adm" not in usernames


async def test_search_by_username_prefix_respects_limit(repo):
    for i in range(5):
        await repo.save(User.create_labeler(id=uuid4(), username=f"user_{i:02d}"))

    results = await repo.search_by_username_prefix("user", role="labeler", limit=3)
    assert len(results) == 3


async def test_search_by_username_prefix_returns_empty_on_no_match(repo):
    await repo.save(User.create_labeler(id=uuid4(), username="alice"))
    results = await repo.search_by_username_prefix("zzz", role="labeler", limit=10)
    assert results == []
