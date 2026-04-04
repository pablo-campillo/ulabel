"""Port interface for image persistence."""

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from ulabel.domain.images import Image


class ImageRepository(ABC):
    """Abstract repository for storing and retrieving images."""

    @abstractmethod
    async def get_by_id(self, image_id: UUID) -> Image | None:
        """Retrieve an image by its unique identifier.

        Args:
            image_id: The unique identifier of the image.

        Returns:
            The image if found, None otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    async def save(self, image: Image) -> None:
        """Persist a single image (insert or update).

        Args:
            image: The image entity to save.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_next_pending(self, project_id: UUID) -> Image | None:
        """Retrieve the next image with PENDING status in a project.

        Args:
            project_id: The project to search within.

        Returns:
            The next pending image, or None if all images are assigned or done.
        """
        raise NotImplementedError

    @abstractmethod
    async def assign_next_pending(
        self, project_id: UUID, labeler_id: UUID, assigned_at: datetime
    ) -> Image | None:
        """Atomically claim the next pending image and assign it to a labeler.

        Selects the next pending image and transitions it to IN_PROGRESS
        within a single transaction to prevent race conditions.

        Args:
            project_id: The project to search within.
            labeler_id: The labeler to assign the image to.
            assigned_at: The assignment timestamp.

        Returns:
            The assigned image, or None if no pending images exist.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_expired_in_progress(self, cutoff: datetime) -> list[Image]:
        """Retrieve all in-progress images assigned before the cutoff time.

        Args:
            cutoff: Images assigned before this timestamp are considered expired.

        Returns:
            A list of expired in-progress images.
        """
        raise NotImplementedError

    @abstractmethod
    async def save_bulk(self, images: list[Image]) -> None:
        """Persist multiple images in a single batch operation.

        Args:
            images: The list of image entities to save.
        """
        raise NotImplementedError
