"""Port interface for the Unit of Work pattern."""

from abc import ABC, abstractmethod
from types import TracebackType

from ulabel.domain.ports.image_repository import ImageRepository
from ulabel.domain.ports.import_job_repository import ImportJobRepository
from ulabel.domain.ports.label_repository import LabelRepository
from ulabel.domain.ports.project_repository import ProjectRepository
from ulabel.domain.ports.stats_repository import StatsRepository
from ulabel.domain.ports.user_repository import UserRepository


class UnitOfWork(ABC):
    """Abstract Unit of Work that manages a shared transaction across repositories.

    Use as an async context manager to open a session shared by all
    repositories. Call ``commit()`` to persist changes; exiting without
    committing rolls back automatically.
    """

    project_repository: ProjectRepository
    image_repository: ImageRepository
    label_repository: LabelRepository
    stats_repository: StatsRepository
    user_repository: UserRepository
    import_job_repository: ImportJobRepository

    @abstractmethod
    async def __aenter__(self) -> "UnitOfWork":
        raise NotImplementedError

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def commit(self) -> None:
        """Commit the current transaction."""
        raise NotImplementedError

    @abstractmethod
    async def rollback(self) -> None:
        """Roll back the current transaction."""
        raise NotImplementedError
