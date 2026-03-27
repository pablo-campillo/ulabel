from datetime import datetime
from uuid import UUID

from ulabel.domain.images import Image, ImageStatus
from ulabel.domain.ports.image_repository import ImageRepository


class InMemoryImageRepository(ImageRepository):

    def __init__(self, images: list[Image] | None = None):
        self._images: dict[UUID, Image] = {i.id: i for i in (images or [])}

    async def get_by_id(self, image_id: UUID) -> Image | None:
        return self._images.get(image_id)

    async def save(self, image: Image) -> None:
        self._images[image.id] = image

    async def get_next_pending(self, project_id: UUID) -> Image | None:
        pending = [
            i for i in self._images.values()
            if i.project_id == project_id and i.status == ImageStatus.PENDING
        ]
        pending.sort(key=lambda i: i.id)
        return pending[0] if pending else None

    async def get_expired_in_progress(self, cutoff: datetime) -> list[Image]:
        return [
            i for i in self._images.values()
            if i.status == ImageStatus.IN_PROGRESS
            and i.assigned_at is not None
            and i.assigned_at < cutoff
        ]

    async def save_bulk(self, images: list[Image]) -> None:
        existing_keys = {(i.project_id, i.storage_key) for i in self._images.values()}
        for image in images:
            if (image.project_id, image.storage_key) not in existing_keys:
                self._images[image.id] = image
                existing_keys.add((image.project_id, image.storage_key))
