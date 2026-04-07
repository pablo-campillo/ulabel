"""SQLAlchemy implementation of the image repository.

Provides PostgreSQL-backed persistence for images using upsert
semantics and row-level locking for concurrent assignment safety.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ulabel.domain.images import Image, ImageStatus
from ulabel.domain.ports.image_repository import ImageRepository
from ulabel.infrastructure.models.image import ImageModel


class SqlAlchemyImageRepository(ImageRepository):
    """PostgreSQL-backed image repository using SQLAlchemy."""

    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]):
        """Initialize with an async session factory.

        Args:
            sessionmaker: Factory for creating async database sessions.
        """
        self._sessionmaker = sessionmaker

    async def get_by_id(self, image_id: UUID) -> Image | None:
        """Retrieve an image by its ID.

        Args:
            image_id: The image's unique identifier.

        Returns:
            The domain Image if found, otherwise None.
        """
        async with self._sessionmaker() as session:
            result = await session.execute(select(ImageModel).where(ImageModel.id == image_id))
            model = result.scalar_one_or_none()
            return model.to_domain() if model else None

    async def save(self, image: Image) -> None:
        """Save or update an image using upsert semantics.

        Args:
            image: The domain Image to persist.
        """
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
        """Get the next pending image for a project using row-level locking.

        Uses ``SELECT ... FOR UPDATE SKIP LOCKED`` to safely handle
        concurrent assignment requests.

        Args:
            project_id: The project to find a pending image in.

        Returns:
            The next pending Image, or None if no images are available.
        """
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

    async def assign_next_pending(
        self, project_id: UUID, labeler_id: UUID, assigned_at: datetime
    ) -> Image | None:
        """Atomically claim the next pending image within a single transaction.

        Uses ``SELECT ... FOR UPDATE SKIP LOCKED`` followed by an update,
        all within the same session, so the row lock is held until commit.

        Args:
            project_id: The project to find a pending image in.
            labeler_id: The labeler to assign the image to.
            assigned_at: The assignment timestamp.

        Returns:
            The assigned Image, or None if no pending images are available.
        """
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
            if model is None:
                return None
            image = model.to_domain()
            image.assign(labeler_id=labeler_id, assigned_at=assigned_at)
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
            return image

    async def expire_in_progress(self, cutoff: datetime) -> list[Image]:
        """Atomically expire stale in-progress images within a single transaction.

        Uses ``SELECT ... FOR UPDATE SKIP LOCKED`` to lock rows, then
        resets each to PENDING via upsert, all within the same session.

        Args:
            cutoff: Images assigned before this time are considered expired.

        Returns:
            A list of images that were expired.
        """
        async with self._sessionmaker() as session:
            result = await session.execute(
                select(ImageModel)
                .where(
                    ImageModel.status == ImageStatus.IN_PROGRESS.value,
                    ImageModel.assigned_at < cutoff,
                )
                .with_for_update(skip_locked=True)
            )
            models = list(result.scalars())
            if not models:
                return []
            expired: list[Image] = []
            for model in models:
                image = model.to_domain()
                image.expire()
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
                expired.append(image)
            await session.commit()
            return expired

    async def get_expired_in_progress(self, cutoff: datetime) -> list[Image]:
        """Find all in-progress images assigned before the cutoff time.

        Args:
            cutoff: Images assigned before this time are considered expired.

        Returns:
            A list of expired in-progress Images.
        """
        async with self._sessionmaker() as session:
            result = await session.execute(
                select(ImageModel).where(
                    ImageModel.status == ImageStatus.IN_PROGRESS.value,
                    ImageModel.assigned_at < cutoff,
                )
            )
            return [m.to_domain() for m in result.scalars()]

    async def save_bulk(self, images: list[Image]) -> None:
        """Bulk-insert images in chunks, skipping duplicates.

        Args:
            images: The list of domain Images to insert.
        """
        if not images:
            return
        chunk_size = 1000
        async with self._sessionmaker() as session:
            for i in range(0, len(images), chunk_size):
                chunk = images[i : i + chunk_size]
                await session.execute(
                    insert(ImageModel)
                    .values(
                        [
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
                        ]
                    )
                    .on_conflict_do_nothing()
                )
            await session.commit()
