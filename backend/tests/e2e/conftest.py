import os
from contextlib import asynccontextmanager
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from ulabel.api.api import api_router
from ulabel.api.error_handlers import domain_error_handler, unhandled_error_handler
from ulabel.api.main import container
from ulabel.domain.errors import DomainError
from ulabel.infrastructure.models.base import Base
from ulabel.infrastructure.models.image import ImageModel  # noqa: F401
from ulabel.infrastructure.models.label import LabelRecordModel  # noqa: F401
from ulabel.infrastructure.models.project import (  # noqa: F401
    ProjectLabelerModel,
    ProjectLabelModel,
    ProjectModel,
)
from ulabel.infrastructure.models.user import UserModel
from ulabel.infrastructure.storage.fake_storage_service import FakeStorageService

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


@pytest.fixture(scope="session")
def engine():
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL not set — skipping e2e tests")
    return create_async_engine(TEST_DATABASE_URL, echo=False)


@pytest.fixture(scope="session")
async def create_tables(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(autouse=True)
async def clean_tables(engine, create_tables):
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
    yield


@pytest.fixture(scope="session")
def test_app(engine):
    from fastapi import FastAPI

    container.config.from_dict(
        {
            "database": {
                "url": TEST_DATABASE_URL,
                "pool_size": 2,
                "max_overflow": 0,
                "pool_recycle": 3600,
            },
            "storage": {
                "endpoint": "http://fake:9000",
                "access_key": "fake",
                "secret_key": "fake",
                "bucket": "test",
                "secure": False,
                "public_endpoint": "",
                "presigned_url_expiry_seconds": 3600,
            },
            "tasks": {
                "image_assignment_timeout_seconds": 60,
                "image_expiry_interval_seconds": 30,
            },
            "observability": {
                "service_name": "ulabel-test",
                "log_level": "WARNING",
                "log_format": "text",
                "tracing": {
                    "enabled": False,
                    "endpoint": "http://localhost:4317",
                    "sample_ratio": 0.0,
                    "force_trace_header": "X-Force-Trace",
                },
                "metrics": {"enabled": False},
            },
        }
    )

    container.engine.reset()
    container.sessionmaker.reset()
    container.storage_service.override(FakeStorageService())

    @asynccontextmanager
    async def test_lifespan(app: FastAPI):
        yield

    app = FastAPI(lifespan=test_lifespan)
    app.container = container
    app.add_exception_handler(DomainError, domain_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
    app.include_router(api_router, prefix="/v1")

    return app


@pytest.fixture
async def client(test_app):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def seed_users(engine, create_tables):
    admin_id = uuid4()
    labeler_id = uuid4()
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        session.add(UserModel(id=admin_id, username="admin", role="admin"))
        session.add(UserModel(id=labeler_id, username="labeler1", role="labeler"))
        await session.commit()
    return {"admin_id": admin_id, "labeler_id": labeler_id}


@pytest.fixture
async def seed_multiple_labelers(engine, create_tables):
    admin_id = uuid4()
    labeler_ids = [uuid4() for _ in range(5)]
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        session.add(UserModel(id=admin_id, username="admin_multi", role="admin"))
        for i, lid in enumerate(labeler_ids):
            session.add(UserModel(id=lid, username=f"labeler_{i}", role="labeler"))
        await session.commit()
    return {"admin_id": admin_id, "labeler_ids": labeler_ids}
