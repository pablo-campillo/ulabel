"""Background task that expires stale in-progress image assignments."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Callable

from ulabel.domain.ports.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)


class ExpireImagesTask:
    """Periodically checks for and expires in-progress images that have exceeded their timeout.

    Runs as a continuous background loop, reverting abandoned assignments
    so the images become available for reassignment.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        timeout: timedelta,
        interval: timedelta,
        now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ):
        """Initialize the task.

        Args:
            uow: Unit of Work for transactional repository access.
            timeout: Duration after which an in-progress image is considered expired.
            interval: Time between expiration check cycles.
            now: Callable returning the current UTC datetime.
        """
        self._uow = uow
        self._timeout = timeout
        self._interval = interval
        self._now = now

    async def run(self) -> None:
        """Run the expiration loop indefinitely."""
        while True:
            await self.tick()
            await asyncio.sleep(self._interval.total_seconds())

    async def tick(self) -> None:
        """Execute a single expiration cycle, expiring all overdue images."""
        cutoff = self._now() - self._timeout
        async with self._uow as uow:
            expired = await uow.image_repository.expire_in_progress(cutoff)
            if expired:
                logger.info("Expired %d stale assignments", len(expired))
            await uow.commit()
