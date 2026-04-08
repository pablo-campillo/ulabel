import os

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from ulabel.infrastructure.models.base import Base
from ulabel.infrastructure.models.image import ImageModel  # noqa: F401
from ulabel.infrastructure.models.label import LabelRecordModel  # noqa: F401
from ulabel.infrastructure.models.project import (  # noqa: F401
    ProjectLabelerModel,
    ProjectLabelModel,
    ProjectModel,
)
from ulabel.infrastructure.models.user import UserModel  # noqa: F401

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


@pytest.fixture(scope="session")
def engine():
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL not set — skipping integration tests")
    return create_async_engine(TEST_DATABASE_URL, echo=False)


@pytest.fixture(scope="session")
async def create_tables(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def sessionmaker(engine, create_tables):
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture
async def session(sessionmaker):
    async with sessionmaker() as s:
        yield s


@pytest.fixture(autouse=True)
async def clean_tables(engine, create_tables):
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
    yield
