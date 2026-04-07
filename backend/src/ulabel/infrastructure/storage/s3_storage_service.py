"""S3/MinIO storage service implementation.

Provides object storage operations (upload, download URLs, listing)
using the aioboto3 async S3 client.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Any

import aioboto3
from botocore.exceptions import ClientError

from ulabel.domain.errors import StorageFull
from ulabel.domain.ports.storage_service import StorageService


class S3StorageService(StorageService):
    """S3-compatible storage service using aioboto3."""

    _MIN_PART_SIZE = 5 * 1024 * 1024  # 5 MB, S3 minimum for non-final parts

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool = False,
        public_endpoint: str | None = None,
    ):
        """Initialize the S3 storage service.

        Args:
            endpoint: Internal S3/MinIO endpoint URL or hostname.
            access_key: AWS/MinIO access key.
            secret_key: AWS/MinIO secret key.
            bucket: Default bucket name.
            secure: Whether to use HTTPS.
            public_endpoint: Optional public-facing endpoint for presigned URLs.
        """
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
        """Create an async S3 client context manager.

        Yields:
            An aioboto3 S3 client connected to the internal endpoint.
        """
        async with self._session.client("s3", endpoint_url=self._endpoint_url) as client:
            yield client

    async def get_presigned_url(self, storage_key: str, expires_in: timedelta) -> str:
        """Generate a presigned GET URL for an object.

        Args:
            storage_key: The object key in the bucket.
            expires_in: How long the URL should remain valid.

        Returns:
            A presigned URL string.
        """
        async with self._session.client("s3", endpoint_url=self._public_endpoint_url) as client:
            url: str = await client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket, "Key": storage_key},
                ExpiresIn=int(expires_in.total_seconds()),
            )
            return url

    async def upload_file(
        self,
        key: str,
        data: bytes,
        content_type: str,
        size: int,
        metadata: dict[str, str] | None = None,
    ) -> None:
        """Upload a file to the storage bucket.

        Args:
            key: The object key to store the file under.
            data: The file content as bytes.
            content_type: The MIME type of the file.
            size: The content length in bytes.
            metadata: Optional metadata to attach to the object.
        """
        async with self._client() as client:
            kwargs: dict[str, Any] = dict(
                Bucket=self._bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
                ContentLength=size,
            )
            if metadata:
                kwargs["Metadata"] = metadata
            await client.put_object(**kwargs)

    async def upload_file_streaming(
        self,
        key: str,
        chunks: AsyncIterator[bytes],
        content_type: str,
        metadata: dict[str, str] | None = None,
    ) -> None:
        """Upload a file by streaming chunks via S3 multipart upload.

        Buffers chunks until reaching the 5 MB minimum part size before
        uploading each part. Aborts the upload on any error.

        Args:
            key: The object key to store the file under.
            chunks: Async iterator yielding byte chunks.
            content_type: The MIME type of the file.
            metadata: Optional metadata to attach to the object.
        """
        async with self._client() as client:
            create_kwargs: dict[str, Any] = {
                "Bucket": self._bucket,
                "Key": key,
                "ContentType": content_type,
            }
            if metadata:
                create_kwargs["Metadata"] = metadata

            response = await client.create_multipart_upload(**create_kwargs)
            upload_id = response["UploadId"]

            parts: list[dict[str, Any]] = []
            part_number = 1
            buffer = bytearray()

            try:
                async for chunk in chunks:
                    buffer.extend(chunk)
                    if len(buffer) >= self._MIN_PART_SIZE:
                        part = await client.upload_part(
                            Bucket=self._bucket,
                            Key=key,
                            UploadId=upload_id,
                            PartNumber=part_number,
                            Body=bytes(buffer),
                        )
                        parts.append({"ETag": part["ETag"], "PartNumber": part_number})
                        part_number += 1
                        buffer.clear()

                # Upload remaining buffer as the final part (can be < 5MB)
                if buffer or not parts:
                    part = await client.upload_part(
                        Bucket=self._bucket,
                        Key=key,
                        UploadId=upload_id,
                        PartNumber=part_number,
                        Body=bytes(buffer),
                    )
                    parts.append({"ETag": part["ETag"], "PartNumber": part_number})

                await client.complete_multipart_upload(
                    Bucket=self._bucket,
                    Key=key,
                    UploadId=upload_id,
                    MultipartUpload={"Parts": parts},
                )
            except ClientError as e:
                await client.abort_multipart_upload(
                    Bucket=self._bucket,
                    Key=key,
                    UploadId=upload_id,
                )
                if e.response["Error"]["Code"] in ("XMinioStorageFull", "NoSuchBucket"):
                    raise StorageFull(str(e)) from e
                raise
            except Exception:
                await client.abort_multipart_upload(
                    Bucket=self._bucket,
                    Key=key,
                    UploadId=upload_id,
                )
                raise

    async def head_object(self, key: str) -> dict[str, str] | None:
        """Retrieve metadata for an object without downloading it.

        Args:
            key: The object key to check.

        Returns:
            A dict of metadata if the object exists, None if not found.
        """
        async with self._client() as client:
            try:
                response = await client.head_object(Bucket=self._bucket, Key=key)
                metadata: dict[str, str] = response.get("Metadata", {})
                return metadata
            except ClientError as e:
                if e.response["Error"]["Code"] == "404":
                    return None
                raise

    async def list_objects(self, prefix: str) -> AsyncIterator[str]:
        """List object keys under a given prefix using pagination.

        Args:
            prefix: The key prefix to filter objects by.

        Yields:
            Object keys matching the prefix.
        """
        async with self._client() as client:
            paginator = client.get_paginator("list_objects_v2")
            async for page in paginator.paginate(Bucket=self._bucket, Prefix=prefix):
                for obj in page.get("Contents", []):
                    yield obj["Key"]

    async def ensure_bucket(self) -> None:
        """Ensure the configured bucket exists, creating it if necessary."""
        async with self._client() as client:
            try:
                await client.head_bucket(Bucket=self._bucket)
            except ClientError:
                await client.create_bucket(Bucket=self._bucket)
