"""In-memory implementation of the Unit of Work for testing."""

from types import TracebackType

from ulabel.domain.ports.image_repository import ImageRepository
from ulabel.domain.ports.import_job_repository import ImportJobRepository
from ulabel.domain.ports.label_repository import LabelRepository
from ulabel.domain.ports.project_repository import ProjectRepository
from ulabel.domain.ports.stats_repository import StatsRepository
from ulabel.domain.ports.unit_of_work import UnitOfWork
from ulabel.domain.ports.user_repository import UserRepository


class InMemoryUnitOfWork(UnitOfWork):
    """In-memory Unit of Work backed by pre-built repository instances.

    ``commit()`` and ``rollback()`` are no-ops since in-memory
    repositories mutate state immediately.
    """

    def __init__(
        self,
        project_repository: ProjectRepository,
        image_repository: ImageRepository,
        label_repository: LabelRepository,
        stats_repository: StatsRepository,
        user_repository: UserRepository,
        import_job_repository: ImportJobRepository,
    ):
        self.project_repository = project_repository
        self.image_repository = image_repository
        self.label_repository = label_repository
        self.stats_repository = stats_repository
        self.user_repository = user_repository
        self.import_job_repository = import_job_repository

    async def __aenter__(self) -> "InMemoryUnitOfWork":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        pass

    async def commit(self) -> None:
        pass

    async def rollback(self) -> None:
        pass
