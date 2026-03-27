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
    return [
        joinedload(ProjectModel.owner),
        selectinload(ProjectModel.label_entries),
        selectinload(ProjectModel.labeler_entries),
    ]


class SqlAlchemyProjectRepository(ProjectRepository):

    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]):
        self._sessionmaker = sessionmaker

    async def get_by_id(self, project_id: UUID) -> Project | None:
        async with self._sessionmaker() as session:
            result = await session.execute(
                select(ProjectModel)
                .where(ProjectModel.id == project_id)
                .options(*_load_options())
            )
            model = result.unique().scalar_one_or_none()
            return model.to_domain() if model else None

    async def get_by_labeler_id(self, labeler_id: UUID) -> list[Project]:
        async with self._sessionmaker() as session:
            result = await session.execute(
                select(ProjectModel)
                .join(ProjectLabelerModel, ProjectModel.id == ProjectLabelerModel.project_id)
                .where(ProjectLabelerModel.labeler_id == labeler_id)
                .options(*_load_options())
            )
            return [row.to_domain() for row in result.unique().scalars()]

    async def get_all(self, limit: int, offset: int) -> PaginatedResult[Project]:
        async with self._sessionmaker() as session:
            count_result = await session.execute(
                select(func.count()).select_from(ProjectModel)
            )
            total = count_result.scalar_one()

            result = await session.execute(
                select(ProjectModel)
                .options(*_load_options())
                .order_by(ProjectModel.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            items = [row.to_domain() for row in result.unique().scalars()]
            return PaginatedResult(items=items, total=total)

    async def save(self, project: Project) -> None:
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
