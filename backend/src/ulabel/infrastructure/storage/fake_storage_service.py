from collections.abc import AsyncIterator
from datetime import timedelta

from ulabel.domain.ports.storage_service import StorageService


class FakeStorageService(StorageService):

    def __init__(self, objects: list[str] | None = None):
        self._objects = objects or []

    async def get_presigned_url(self, storage_key: str, expires_in: timedelta) -> str:
        return f"http://fake-storage/{storage_key}?expires_in={int(expires_in.total_seconds())}"

    async def upload_file(
        self, key: str, data: bytes, content_type: str, size: int, metadata: dict[str, str] | None = None
    ) -> None:
        pass

    async def head_object(self, key: str) -> dict[str, str] | None:
        return None

    async def list_objects(self, prefix: str) -> AsyncIterator[str]:
        for key in self._objects:
            if key.startswith(prefix):
                yield key

    async def ensure_bucket(self) -> None:
        pass
