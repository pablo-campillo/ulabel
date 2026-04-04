"""Port interface for object storage operations."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from datetime import timedelta


class StorageService(ABC):
    """Abstract service for interacting with an object storage backend."""

    @abstractmethod
    async def get_presigned_url(self, storage_key: str, expires_in: timedelta) -> str:
        """Generate a time-limited presigned URL for downloading an object.

        Args:
            storage_key: The key identifying the stored object.
            expires_in: Duration after which the URL expires.

        Returns:
            A presigned URL string.
        """
        raise NotImplementedError

    @abstractmethod
    async def upload_file(
        self, key: str, data: bytes, content_type: str, size: int, metadata: dict[str, str] | None = None
    ) -> None:
        """Upload a file to object storage.

        Args:
            key: The storage key for the uploaded object.
            data: Raw file bytes.
            content_type: MIME type of the file.
            size: Size of the file in bytes.
            metadata: Optional metadata to attach to the object.
        """
        raise NotImplementedError

    @abstractmethod
    async def upload_file_streaming(
        self,
        key: str,
        chunks: AsyncIterator[bytes],
        content_type: str,
        metadata: dict[str, str] | None = None,
    ) -> None:
        """Upload a file to object storage by streaming chunks.

        Uses multipart upload internally. The caller provides an async
        iterator of byte chunks; the implementation buffers them into
        parts of at least 5 MB before uploading each part.

        Args:
            key: The storage key for the uploaded object.
            chunks: Async iterator yielding byte chunks.
            content_type: MIME type of the file.
            metadata: Optional metadata to attach to the object.
        """
        raise NotImplementedError

    @abstractmethod
    async def head_object(self, key: str) -> dict[str, str] | None:
        """Retrieve metadata for an object without downloading its contents.

        Args:
            key: The storage key of the object.

        Returns:
            A dictionary of object metadata, or None if the object does not exist.
        """
        raise NotImplementedError

    @abstractmethod
    def list_objects(self, prefix: str) -> AsyncIterator[str]:
        """List object keys matching a given prefix.

        Args:
            prefix: The key prefix to filter by.

        Returns:
            An async iterator yielding matching object keys.
        """
        raise NotImplementedError

    @abstractmethod
    async def ensure_bucket(self) -> None:
        """Ensure the storage bucket exists, creating it if necessary."""
        raise NotImplementedError
