from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from ulabel.domain.images import Image


class ImageRepository(ABC):

    @abstractmethod
    async def get_by_id(self, image_id: UUID) -> Image | None:
        raise NotImplementedError

    @abstractmethod
    async def save(self, image: Image) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_next_pending(self, project_id: UUID) -> Image | None:
        raise NotImplementedError

    @abstractmethod
    async def get_expired_in_progress(self, cutoff: datetime) -> list[Image]:
        raise NotImplementedError

    @abstractmethod
    async def save_bulk(self, images: list[Image]) -> None:
        raise NotImplementedError
