from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ulabel.domain.images import Image, ImageStatus
from ulabel.domain.ports.image_repository import ImageRepository
from ulabel.infrastructure.models.image import ImageModel


class SqlAlchemyImageRepository(ImageRepository):

    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]):
        self._sessionmaker = sessionmaker

    async def get_by_id(self, image_id: UUID) -> Image | None:
        async with self._sessionmaker() as session:
            result = await session.execute(
                select(ImageModel).where(ImageModel.id == image_id)
            )
            model = result.scalar_one_or_none()
            return model.to_domain() if model else None

    async def save(self, image: Image) -> None:
        async with self._sessionmaker() as session:
            stmt = (
                insert(ImageModel)
                .values(
                    id=image.id,
                    project_id=image.project_id,
                    storage_key=image.storage_key,
                    status=image.status.value,
                    labeler_id=image.labeler_id,
                    assigned_at=image.assigned_at,
                    assignment_id=image.assignment_id,
                )
                .on_conflict_do_update(
                    index_elements=["id"],
                    set_={
                        "status": image.status.value,
                        "labeler_id": image.labeler_id,
                        "assigned_at": image.assigned_at,
                        "assignment_id": image.assignment_id,
                    },
                )
            )
            await session.execute(stmt)
            await session.commit()

    async def get_next_pending(self, project_id: UUID) -> Image | None:
        async with self._sessionmaker() as session:
            result = await session.execute(
                select(ImageModel)
                .where(
                    ImageModel.project_id == project_id,
                    ImageModel.status == ImageStatus.PENDING.value,
                )
                .order_by(ImageModel.id)
                .limit(1)
                .with_for_update(skip_locked=True)
            )
            model = result.scalar_one_or_none()
            return model.to_domain() if model else None

    async def get_expired_in_progress(self, cutoff: datetime) -> list[Image]:
        async with self._sessionmaker() as session:
            result = await session.execute(
                select(ImageModel).where(
                    ImageModel.status == ImageStatus.IN_PROGRESS.value,
                    ImageModel.assigned_at < cutoff,
                )
            )
            return [m.to_domain() for m in result.scalars()]

    async def save_bulk(self, images: list[Image]) -> None:
        if not images:
            return
        chunk_size = 1000
        async with self._sessionmaker() as session:
            for i in range(0, len(images), chunk_size):
                chunk = images[i : i + chunk_size]
                await session.execute(
                    insert(ImageModel)
                    .values([
                        {
                            "id": img.id,
                            "project_id": img.project_id,
                            "storage_key": img.storage_key,
                            "status": img.status.value,
                            "labeler_id": img.labeler_id,
                            "assigned_at": img.assigned_at,
                            "assignment_id": img.assignment_id,
                        }
                        for img in chunk
                    ])
                    .on_conflict_do_nothing()
                )
            await session.commit()
