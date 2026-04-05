"""Fake storage service implementation for testing.

Returns predictable URLs and performs no actual I/O.
"""

from collections.abc import AsyncIterator
from datetime import timedelta

from ulabel.domain.ports.storage_service import StorageService


class FakeStorageService(StorageService):
    """No-op storage service that returns fake URLs for testing."""

    def __init__(self, objects: list[str] | None = None):
        """Initialize with optional pre-existing object keys.

        Args:
            objects: Optional list of object keys to simulate in the bucket.
        """
        self._objects = objects or []
        self._uploaded: dict[str, dict] = {}

    async def get_presigned_url(self, storage_key: str, expires_in: timedelta) -> str:
        return f"http://fake-storage/{storage_key}?expires_in={int(expires_in.total_seconds())}"

    async def upload_file(
        self,
        key: str,
        data: bytes,
        content_type: str,
        size: int,
        metadata: dict[str, str] | None = None,
    ) -> None:
        self._uploaded[key] = {"data": data, "metadata": metadata or {}}

    async def upload_file_streaming(
        self,
        key: str,
        chunks: AsyncIterator[bytes],
        content_type: str,
        metadata: dict[str, str] | None = None,
    ) -> None:
        collected = bytearray()
        async for chunk in chunks:
            collected.extend(chunk)
        self._uploaded[key] = {"data": bytes(collected), "metadata": metadata or {}}

    async def head_object(self, key: str) -> dict[str, str] | None:
        if key in self._uploaded:
            return self._uploaded[key]["metadata"]
        return None

    async def list_objects(self, prefix: str) -> AsyncIterator[str]:
        for key in self._objects:
            if key.startswith(prefix):
                yield key

    async def ensure_bucket(self) -> None:
        pass
