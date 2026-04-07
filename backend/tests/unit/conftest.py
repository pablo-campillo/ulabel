from uuid import uuid4

import pytest

from ulabel.domain.ports.image_repository import ImageRepository
from ulabel.domain.ports.import_job_repository import ImportJobRepository
from ulabel.domain.ports.label_repository import LabelRepository
from ulabel.domain.ports.project_repository import ProjectRepository
from ulabel.domain.ports.stats_repository import StatsRepository
from ulabel.domain.ports.user_repository import UserRepository
from ulabel.domain.users import User
from ulabel.infrastructure.repositories.in_memory.image_repository import InMemoryImageRepository
from ulabel.infrastructure.repositories.in_memory.import_job_repository import (
    InMemoryImportJobRepository,
)
from ulabel.infrastructure.repositories.in_memory.label_repository import InMemoryLabelRepository
from ulabel.infrastructure.repositories.in_memory.project_repository import (
    InMemoryProjectRepository,
)
from ulabel.infrastructure.repositories.in_memory.stats_repository import InMemoryStatsRepository
from ulabel.infrastructure.repositories.in_memory.unit_of_work import InMemoryUnitOfWork
from ulabel.infrastructure.repositories.in_memory.user_repository import InMemoryUserRepository


@pytest.fixture
def admin():
    return User.create_admin(id=uuid4(), username="admin")


@pytest.fixture
def labeler():
    return User.create_labeler(id=uuid4(), username="labeler")


def make_uow(
    *,
    project_repository: ProjectRepository | None = None,
    image_repository: ImageRepository | None = None,
    label_repository: LabelRepository | None = None,
    stats_repository: StatsRepository | None = None,
    user_repository: UserRepository | None = None,
    import_job_repository: ImportJobRepository | None = None,
) -> InMemoryUnitOfWork:
    """Build an InMemoryUnitOfWork with sensible defaults for missing repos."""
    return InMemoryUnitOfWork(
        project_repository=project_repository or InMemoryProjectRepository(),
        image_repository=image_repository or InMemoryImageRepository(),
        label_repository=label_repository or InMemoryLabelRepository(),
        stats_repository=stats_repository or InMemoryStatsRepository([], [], {}),
        user_repository=user_repository or InMemoryUserRepository(),
        import_job_repository=import_job_repository or InMemoryImportJobRepository(),
    )
