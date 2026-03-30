"""Use case for exporting labeled data from a project as CSV or JSON."""

import csv
import io
import json
from datetime import date, timedelta
from enum import Enum
from uuid import UUID

from ulabel.application.add_labeler_to_project import ProjectNotFound
from ulabel.domain.errors import DomainError
from ulabel.domain.ports.label_repository import LabelRepository
from ulabel.domain.ports.project_repository import ProjectRepository
from ulabel.domain.ports.storage_service import StorageService


class ExportFormat(str, Enum):
    """Supported export file formats."""

    JSON = "json"
    CSV = "csv"


class NoLabelsFound(DomainError):
    """Raised when a project has no labels to export."""

    pass


PRESIGNED_URL_EXPIRY = timedelta(hours=1)


class ExportLabelsUseCase:
    """Generates and uploads a label export file, returning a presigned download URL.

    Caches exports in object storage and reuses them when the label count
    has not changed since the last export.
    """

    def __init__(
        self,
        project_repository: ProjectRepository,
        label_repository: LabelRepository,
        storage_service: StorageService,
    ):
        """Initialize the use case.

        Args:
            project_repository: Repository for project lookups.
            label_repository: Repository for label data retrieval.
            storage_service: Service for file upload and presigned URL generation.
        """
        self._project_repository = project_repository
        self._label_repository = label_repository
        self._storage_service = storage_service

    async def execute(self, project_id: UUID, fmt: ExportFormat) -> str:
        """Export all labels for a project in the specified format.

        Args:
            project_id: The project whose labels to export.
            fmt: The desired output format.

        Returns:
            A presigned URL to download the export file.

        Raises:
            ProjectNotFound: If the project does not exist.
            NoLabelsFound: If the project has no labels to export.
        """
        project = await self._project_repository.get_by_id(project_id)
        if project is None:
            raise ProjectNotFound("Project not found")

        label_count = await self._label_repository.count_by_project(project_id)
        if label_count == 0:
            raise NoLabelsFound("No labels to export")

        filename = f"{project_id}.{fmt.value}"
        storage_key = f"exports/{project_id}/{filename}"

        metadata = await self._storage_service.head_object(storage_key)
        if metadata is not None and metadata.get("label_count") == str(label_count):
            return await self._storage_service.get_presigned_url(storage_key, expires_in=PRESIGNED_URL_EXPIRY)

        rows = await self._label_repository.get_export_data(project_id)

        if fmt == ExportFormat.CSV:
            data, content_type = self._generate_csv(rows)
        else:
            data, content_type = self._generate_json(rows)

        await self._storage_service.upload_file(
            key=storage_key,
            data=data,
            content_type=content_type,
            size=len(data),
            metadata={"label_count": str(label_count)},
        )

        return await self._storage_service.get_presigned_url(storage_key, expires_in=PRESIGNED_URL_EXPIRY)

    @staticmethod
    def _generate_csv(rows) -> tuple[bytes, str]:
        """Generate CSV bytes from label export rows.

        Args:
            rows: Iterable of label export row objects with image_id, storage_key, and value.

        Returns:
            A tuple of the CSV content as bytes and the content type string.
        """
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["image_id", "storage_key", "value"])
        for row in rows:
            writer.writerow([str(row.image_id), row.storage_key, row.value])
        return output.getvalue().encode("utf-8"), "text/csv"

    @staticmethod
    def _generate_json(rows) -> tuple[bytes, str]:
        """Generate JSON bytes from label export rows.

        Args:
            rows: Iterable of label export row objects with image_id, storage_key, and value.

        Returns:
            A tuple of the JSON content as bytes and the content type string.
        """
        data = [
            {"image_id": str(row.image_id), "storage_key": row.storage_key, "value": row.value}
            for row in rows
        ]
        return json.dumps(data, indent=2).encode("utf-8"), "application/json"
