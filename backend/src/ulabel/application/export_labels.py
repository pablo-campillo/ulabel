"""Use case for exporting labeled data from a project as CSV or JSON."""

import csv
import io
import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import timedelta
from enum import Enum
from uuid import UUID

from ulabel.application.add_labeler_to_project import ProjectNotFound
from ulabel.domain.errors import DomainError
from ulabel.domain.labels import LabelExportRow
from ulabel.domain.ports.storage_service import StorageService
from ulabel.domain.ports.unit_of_work import UnitOfWork


class ExportFormat(str, Enum):
    """Supported export file formats."""

    JSON = "json"
    CSV = "csv"


class NoLabelsFound(DomainError):
    """Raised when a project has no labels to export."""

    pass


@dataclass(frozen=True)
class ExportResult:
    """Result of an export operation."""

    url: str
    cache_hit: bool


class ExportLabelsUseCase:
    """Generates and uploads a label export file, returning a presigned download URL.

    Caches exports in object storage and reuses them when the label count
    has not changed since the last export.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        storage_service: StorageService,
        presigned_url_expiry: timedelta,
    ):
        """Initialize the use case.

        Args:
            uow: Unit of Work for transactional repository access.
            storage_service: Service for file upload and presigned URL generation.
            presigned_url_expiry: How long presigned download URLs remain valid.
        """
        self._uow = uow
        self._storage_service = storage_service
        self._presigned_url_expiry = presigned_url_expiry

    async def execute(self, project_id: UUID, fmt: ExportFormat) -> ExportResult:
        """Export all labels for a project in the specified format.

        Args:
            project_id: The project whose labels to export.
            fmt: The desired output format.

        Returns:
            An ExportResult with the presigned URL and cache-hit flag.

        Raises:
            ProjectNotFound: If the project does not exist.
            NoLabelsFound: If the project has no labels to export.
        """
        async with self._uow as uow:
            project = await uow.project_repository.get_by_id(project_id)
            if project is None:
                raise ProjectNotFound("Project not found")

            label_count = await uow.label_repository.count_by_project(project_id)
            if label_count == 0:
                raise NoLabelsFound("No labels to export")

            filename = f"{project_id}.{fmt.value}"
            storage_key = f"exports/{project_id}/{filename}"

            metadata = await self._storage_service.head_object(storage_key)
            if metadata is not None and metadata.get("label_count") == str(label_count):
                url = await self._storage_service.get_presigned_url(
                    storage_key,
                    expires_in=self._presigned_url_expiry,
                )
                return ExportResult(url=url, cache_hit=True)

            rows = uow.label_repository.get_export_data(project_id)

            if fmt == ExportFormat.CSV:
                chunks = self._generate_csv(rows)
                content_type = "text/csv"
            else:
                chunks = self._generate_json(rows)
                content_type = "application/json"

            await self._storage_service.upload_file_streaming(
                key=storage_key,
                chunks=chunks,
                content_type=content_type,
                metadata={"label_count": str(label_count)},
            )

            url = await self._storage_service.get_presigned_url(
                storage_key,
                expires_in=self._presigned_url_expiry,
            )
            return ExportResult(url=url, cache_hit=False)

    @staticmethod
    async def _generate_csv(rows: AsyncIterator[LabelExportRow]) -> AsyncIterator[bytes]:
        """Generate CSV bytes from label export rows as a stream.

        Args:
            rows: Async iterator of label export row objects.

        Yields:
            CSV content as byte chunks (header first, then one chunk per row).
        """
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["image_id", "storage_key", "value"])
        yield output.getvalue().encode("utf-8")

        async for row in rows:
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow([str(row.image_id), row.storage_key, row.value])
            yield output.getvalue().encode("utf-8")

    @staticmethod
    async def _generate_json(rows: AsyncIterator[LabelExportRow]) -> AsyncIterator[bytes]:
        """Generate JSON bytes from label export rows as a stream.

        Args:
            rows: Async iterator of label export row objects.

        Yields:
            JSON content as byte chunks forming a valid JSON array.
        """
        yield b"[\n"
        first = True
        async for row in rows:
            if not first:
                yield b",\n"
            else:
                first = False
            entry = json.dumps(
                {"image_id": str(row.image_id), "storage_key": row.storage_key, "value": row.value},
                indent=2,
            )
            yield entry.encode("utf-8")
        yield b"\n]"
