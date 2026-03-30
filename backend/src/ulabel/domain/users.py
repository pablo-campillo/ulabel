"""Domain model for users and their roles."""

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class UserRole(StrEnum):
    """Available roles that a user can hold in the system."""

    ADMIN = "admin"
    LABELER = "labeler"


@dataclass
class User:
    """A user of the labeling platform.

    Attributes:
        id: Unique identifier for the user.
        username: The user's display name / login handle.
        role: The user's role determining their permissions.
    """

    id: UUID
    username: str
    role: UserRole

    @classmethod
    def create_admin(cls, id: UUID, username: str) -> "User":
        """Create a user with the ADMIN role.

        Args:
            id: Unique identifier for the user.
            username: The user's display name.

        Returns:
            A new User instance with ADMIN role.
        """
        return cls(id=id, username=username, role=UserRole.ADMIN)

    @classmethod
    def create_labeler(cls, id: UUID, username: str) -> "User":
        """Create a user with the LABELER role.

        Args:
            id: Unique identifier for the user.
            username: The user's display name.

        Returns:
            A new User instance with LABELER role.
        """
        return cls(id=id, username=username, role=UserRole.LABELER)
