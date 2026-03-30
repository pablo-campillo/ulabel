"""SQLAlchemy implementation of the project repository.

Provides PostgreSQL-backed persistence for projects with eager loading
of related labels and labelers, and full upsert support.
"""

from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import joinedload, selectinload

from ulabel.domain.pagination import PaginatedResult
from ulabel.domain.ports.project_repository import ProjectRepository
from ulabel.domain.projects import Project
from ulabel.infrastructure.models.project import ProjectLabelModel, ProjectLabelerModel, ProjectModel


def _load_options():
    """Return SQLAlchemy eager-loading options for project queries.

    Returns:
        A list of load options for owner, labels, and labelers.
    """
    return [
        joinedload(ProjectModel.owner),
        selectinload(ProjectModel.label_entries),
        selectinload(ProjectModel.labeler_entries),
    ]


class SqlAlchemyProjectRepository(ProjectRepository):
    """PostgreSQL-backed project repository using SQLAlchemy."""

    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]):
        """Initialize with an async session factory.

        Args:
            sessionmaker: Factory for creating async database sessions.
        """
        self._sessionmaker = sessionmaker

    async def get_by_id(self, project_id: UUID) -> Project | None:
        """Retrieve a project by its ID with all relations loaded.

        Args:
            project_id: The project's unique identifier.

        Returns:
            The domain Project if found, otherwise None.
        """
        async with self._sessionmaker() as session:
            result = await session.execute(
                select(ProjectModel)
                .where(ProjectModel.id == project_id)
                .options(*_load_options())
            )
            model = result.unique().scalar_one_or_none()
            return model.to_domain() if model else None

    async def get_by_name(self, name: str) -> Project | None:
        """Retrieve a project by its unique name.

        Args:
            name: The project name to look up.

        Returns:
            The domain Project if found, otherwise None.
        """
        async with self._sessionmaker() as session:
            result = await session.execute(
                select(ProjectModel)
                .where(ProjectModel.name == name)
                .options(*_load_options())
            )
            model = result.unique().scalar_one_or_none()
            return model.to_domain() if model else None

    async def get_by_labeler_id(self, labeler_id: UUID) -> list[Project]:
        """Retrieve all projects that a labeler is assigned to.

        Args:
            labeler_id: The labeler's user ID.

        Returns:
            A list of domain Projects the labeler belongs to.
        """
        async with self._sessionmaker() as session:
            result = await session.execute(
                select(ProjectModel)
                .join(ProjectLabelerModel, ProjectModel.id == ProjectLabelerModel.project_id)
                .where(ProjectLabelerModel.labeler_id == labeler_id)
                .options(*_load_options())
            )
            return [row.to_domain() for row in result.unique().scalars()]

    async def get_all(self, limit: int, offset: int, *, name: str | None = None) -> PaginatedResult[Project]:
        """Retrieve a paginated list of projects, optionally filtered by name.

        Args:
            limit: Maximum number of projects to return.
            offset: Number of projects to skip.
            name: Optional case-insensitive name filter (contains match).

        Returns:
            A PaginatedResult with projects ordered by creation date (newest first).
        """
        async with self._sessionmaker() as session:
            filters = []
            if name is not None:
                filters.append(ProjectModel.name.ilike(f"%{name}%"))

            count_result = await session.execute(
                select(func.count()).select_from(ProjectModel).where(*filters)
            )
            total = count_result.scalar_one()

            result = await session.execute(
                select(ProjectModel)
                .where(*filters)
                .options(*_load_options())
                .order_by(ProjectModel.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            items = [row.to_domain() for row in result.unique().scalars()]
            return PaginatedResult(items=items, total=total)

    async def save(self, project: Project) -> None:
        """Save or update a project with its labels and labelers.

        Uses upsert for the project row and replaces all label and
        labeler associations on each save.

        Args:
            project: The domain Project to persist.
        """
        async with self._sessionmaker() as session:
            # Upsert project row
            await session.execute(
                insert(ProjectModel)
                .values(
                    id=project.id,
                    owner_id=project.owner.id,
                    name=project.name,
                    description=project.description,
                )
                .on_conflict_do_update(
                    index_elements=["id"],
                    set_={"name": project.name, "description": project.description},
                )
            )

            # Replace labels: delete existing, insert current
            await session.execute(
                delete(ProjectLabelModel).where(ProjectLabelModel.project_id == project.id)
            )
            if project.labels:
                await session.execute(
                    insert(ProjectLabelModel),
                    [{"project_id": project.id, "label": label} for label in project.labels],
                )

            # Replace labelers: delete existing, insert current
            await session.execute(
                delete(ProjectLabelerModel).where(ProjectLabelerModel.project_id == project.id)
            )
            if project.labeler_ids:
                await session.execute(
                    insert(ProjectLabelerModel),
                    [{"project_id": project.id, "labeler_id": lid} for lid in project.labeler_ids],
                )

            await session.commit()
