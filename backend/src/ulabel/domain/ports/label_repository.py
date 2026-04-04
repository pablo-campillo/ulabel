"""Port interface for label persistence."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from uuid import UUID

from ulabel.domain.labels import LabelExportRow, LabelRecord


class LabelRepository(ABC):
    """Abstract repository for storing and querying label records."""

    @abstractmethod
    async def save(self, label_record: LabelRecord) -> None:
        """Persist a single label record.

        Args:
            label_record: The label record to save.
        """
        raise NotImplementedError

    @abstractmethod
    async def count_by_project(self, project_id: UUID) -> int:
        """Count the total number of labels in a project.

        Args:
            project_id: The project to count labels for.

        Returns:
            The total label count.
        """
        raise NotImplementedError

    @abstractmethod
    def get_export_data(self, project_id: UUID) -> AsyncIterator[LabelExportRow]:
        """Retrieve flattened label rows for export as an async stream.

        Args:
            project_id: The project to export labels from.

        Yields:
            Export rows containing image and label information.
        """
        raise NotImplementedError
