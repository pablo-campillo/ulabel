import asyncio
import os
from logging.config import fileConfig

from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context
from ulabel.infrastructure.models.base import Base
from ulabel.infrastructure.models.image import ImageModel  # noqa: F401
from ulabel.infrastructure.models.import_job import ImportJobModel  # noqa: F401
from ulabel.infrastructure.models.label import LabelRecordModel  # noqa: F401
from ulabel.infrastructure.models.project import (  # noqa: F401
    ProjectLabelerModel,
    ProjectLabelModel,
    ProjectModel,
)
from ulabel.infrastructure.models.user import UserModel  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+asyncpg://ulabel:secret@localhost:5432/ulabel"
)


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


asyncio.run(run_migrations_online())
