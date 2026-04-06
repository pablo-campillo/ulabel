from uuid import uuid4

import pytest

from ulabel.application.search_labelers import SearchLabelersUseCase
from ulabel.domain.users import User
from ulabel.infrastructure.repositories.in_memory.user_repository import InMemoryUserRepository


@pytest.fixture
def labelers():
    return [
        User.create_labeler(id=uuid4(), username="alice"),
        User.create_labeler(id=uuid4(), username="alicia"),
        User.create_labeler(id=uuid4(), username="bob"),
    ]


@pytest.fixture
def admin():
    return User.create_admin(id=uuid4(), username="alvaro")


@pytest.fixture
def use_case(labelers, admin):
    return SearchLabelersUseCase(
        user_repository=InMemoryUserRepository(users=[*labelers, admin])
    )


async def test_returns_labelers_matching_prefix(use_case):
    results = await use_case.execute(prefix="ali")
    usernames = [u.username for u in results]
    assert usernames == ["alice", "alicia"]


async def test_excludes_admins(use_case):
    results = await use_case.execute(prefix="al")
    usernames = [u.username for u in results]
    assert "alvaro" not in usernames


async def test_returns_empty_when_no_match(use_case):
    results = await use_case.execute(prefix="zzz")
    assert results == []


async def test_respects_limit(use_case):
    results = await use_case.execute(prefix="al", limit=1)
    assert len(results) == 1


async def test_case_insensitive(use_case):
    results = await use_case.execute(prefix="ALI")
    usernames = [u.username for u in results]
    assert usernames == ["alice", "alicia"]
