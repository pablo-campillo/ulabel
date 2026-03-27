from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from datetime import timedelta


class StorageService(ABC):

    @abstractmethod
    async def get_presigned_url(self, storage_key: str, expires_in: timedelta) -> str:
        raise NotImplementedError

    @abstractmethod
    async def upload_file(
        self, key: str, data: bytes, content_type: str, size: int, metadata: dict[str, str] | None = None
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def head_object(self, key: str) -> dict[str, str] | None:
        raise NotImplementedError

    @abstractmethod
    def list_objects(self, prefix: str) -> AsyncIterator[str]:
        raise NotImplementedError

    @abstractmethod
    async def ensure_bucket(self) -> None:
        raise NotImplementedError
