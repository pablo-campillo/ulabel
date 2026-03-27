import asyncio
from datetime import datetime, timedelta, timezone
from typing import Callable

from ulabel.domain.ports.image_repository import ImageRepository


class ExpireImagesTask:

    def __init__(
        self,
        image_repository: ImageRepository,
        timeout: timedelta,
        interval: timedelta,
        now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ):
        self._image_repository = image_repository
        self._timeout = timeout
        self._interval = interval
        self._now = now

    async def run(self) -> None:
        while True:
            await self.tick()
            await asyncio.sleep(self._interval.total_seconds())

    async def tick(self) -> None:
        cutoff = self._now() - self._timeout
        expired = await self._image_repository.get_expired_in_progress(cutoff)
        for image in expired:
            image.expire()
            await self._image_repository.save(image)
