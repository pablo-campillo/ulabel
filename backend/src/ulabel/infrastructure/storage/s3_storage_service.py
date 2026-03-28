from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Any

import aioboto3
from botocore.exceptions import ClientError

from ulabel.domain.ports.storage_service import StorageService


class S3StorageService(StorageService):

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool = False,
        public_endpoint: str | None = None,
    ):
        self._session = aioboto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )
        scheme = "https" if secure else "http"
        self._endpoint_url = (
            endpoint if endpoint.startswith(("http://", "https://")) else f"{scheme}://{endpoint}"
        )
        if public_endpoint:
            self._public_endpoint_url = (
                public_endpoint
                if public_endpoint.startswith(("http://", "https://"))
                else f"{scheme}://{public_endpoint}"
            )
        else:
            self._public_endpoint_url = self._endpoint_url
        self._bucket = bucket

    @asynccontextmanager
    async def _client(self) -> Any:
        async with self._session.client("s3", endpoint_url=self._endpoint_url) as client:
            yield client

    async def get_presigned_url(self, storage_key: str, expires_in: timedelta) -> str:
        async with self._session.client("s3", endpoint_url=self._public_endpoint_url) as client:
            url: str = await client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket, "Key": storage_key},
                ExpiresIn=int(expires_in.total_seconds()),
            )
            return url

    async def upload_file(
        self, key: str, data: bytes, content_type: str, size: int, metadata: dict[str, str] | None = None
    ) -> None:
        async with self._client() as client:
            kwargs: dict = dict(
                Bucket=self._bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
                ContentLength=size,
            )
            if metadata:
                kwargs["Metadata"] = metadata
            await client.put_object(**kwargs)

    async def head_object(self, key: str) -> dict[str, str] | None:
        async with self._client() as client:
            try:
                response = await client.head_object(Bucket=self._bucket, Key=key)
                return response.get("Metadata", {})
            except ClientError as e:
                if e.response["Error"]["Code"] == "404":
                    return None
                raise

    async def list_objects(self, prefix: str) -> AsyncIterator[str]:
        async with self._client() as client:
            paginator = client.get_paginator("list_objects_v2")
            async for page in paginator.paginate(Bucket=self._bucket, Prefix=prefix):
                for obj in page.get("Contents", []):
                    yield obj["Key"]

    async def ensure_bucket(self) -> None:
        async with self._client() as client:
            try:
                await client.head_bucket(Bucket=self._bucket)
            except ClientError:
                await client.create_bucket(Bucket=self._bucket)
