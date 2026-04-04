"""Application-layer data transfer objects."""

from dataclasses import dataclass
from uuid import UUID

from ulabel.domain.projects import Project


@dataclass
class ResolvedLabeler:
    """A labeler with resolved identity information.

    Attributes:
        id: The labeler's unique identifier.
        username: The labeler's display name.
    """

    id: UUID
    username: str


@dataclass
class ProjectWithLabelers:
    """A project together with its resolved labeler details.

    Attributes:
        project: The domain project entity.
        labelers: Labelers with resolved usernames.
    """

    project: Project
    labelers: list[ResolvedLabeler]
