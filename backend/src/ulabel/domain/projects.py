"""Domain model for labeling projects."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID

from ulabel.domain.users import User


@dataclass
class Project:
    """A labeling project that groups images, labels, and labelers.

    Attributes:
        id: Unique identifier for the project.
        owner: The admin user who owns the project.
        name: Human-readable project name.
        description: Free-text description of the project.
        labels: Set of allowed label values for this project.
        created_at: Timestamp when the project was created.
        labeler_ids: Set of user identifiers assigned as labelers.
    """

    id: UUID
    owner: User
    name: str
    description: str
    labels: set[str]
    created_at: datetime | None = None
    labeler_ids: set[UUID] = field(default_factory=set)

    @classmethod
    def create(cls, id: UUID, owner: User, name: str, description: str, labels: set[str], created_at: datetime | None = None) -> "Project":
        """Create a new project, defaulting created_at to the current UTC time.

        Args:
            id: Unique identifier for the project.
            owner: The admin user who owns the project.
            name: Human-readable project name.
            description: Free-text description.
            labels: Set of allowed label values.
            created_at: Optional creation timestamp; defaults to now (UTC).

        Returns:
            A new Project instance.
        """
        if created_at is None:
            created_at = datetime.now(timezone.utc)
        return cls(id=id, owner=owner, name=name, description=description, labels=labels, created_at=created_at)

    def add_labeler(self, labeler_id: UUID) -> None:
        """Add a labeler to the project.

        Args:
            labeler_id: Identifier of the labeler to add.
        """
        self.labeler_ids.add(labeler_id)

    def update(self, *, name: str | None = None, description: str | None = None) -> None:
        """Update mutable project fields.

        Only the provided (non-None) fields are updated.

        Args:
            name: New project name, if changing.
            description: New project description, if changing.
        """
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description

    def set_labelers(self, labeler_ids: set[UUID]) -> None:
        """Replace the full set of assigned labelers.

        Args:
            labeler_ids: The new set of labeler identifiers.
        """
        self.labeler_ids = labeler_ids
