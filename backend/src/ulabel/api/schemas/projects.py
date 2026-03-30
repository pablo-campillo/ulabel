"""Pydantic schemas for project-related requests and responses."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from ulabel.api.schemas.pagination import PaginatedResponse


class CreateProjectRequest(BaseModel):
    """Request body for creating a new labelling project."""
    owner_id: UUID = Field(..., description="ID of the `admin` user who will own the project.")
    name: str = Field(..., description="Project name.", examples=["Vehicle classification"])
    description: str = Field(..., description="Detailed description of the project goal.")
    labels: set[str] = Field(..., description="Set of labels available for annotating images.")

    model_config = {
        "json_schema_extra": {
            "example": {
                "owner_id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Vehicle classification",
                "description": "Annotate urban traffic images indicating the type of vehicle present.",
                "labels": ["car", "truck", "motorcycle", "bicycle"],
            }
        }
    }


class AddLabelerRequest(BaseModel):
    """Request body for adding a labeler to a project."""

    labeler_id: UUID = Field(..., description="ID of the `labeler` user to add to the project.")

    model_config = {
        "json_schema_extra": {
            "example": {"labeler_id": "456e7890-e89b-12d3-a456-426614174001"}
        }
    }


class UpdateProjectRequest(BaseModel):
    """Request body for updating a project's mutable fields."""

    name: str | None = Field(None, description="New project name.")
    description: str | None = Field(None, description="New project description.")
    labeler_ids: list[UUID] | None = Field(None, description="Full list of labeler IDs to assign.")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Updated name",
                "description": "Updated description",
                "labeler_ids": ["456e7890-e89b-12d3-a456-426614174001"],
            }
        }
    }


class LabelerInfo(BaseModel):
    """Summary information for a labeler assigned to a project."""

    id: UUID = Field(..., description="Labeler user ID.")
    username: str = Field(..., description="Labeler username.")


class ProjectResponse(BaseModel):
    """Response body for a project resource."""

    id: UUID = Field(..., description="Unique project identifier.")
    owner_id: UUID = Field(..., description="ID of the admin owner.")
    name: str = Field(..., description="Project name.")
    description: str = Field(..., description="Project description.")
    labels: set[str] = Field(..., description="Labels available in the project.")
    labelers: list[LabelerInfo] = Field(default_factory=list, description="Assigned labelers.")
    created_at: datetime = Field(..., description="Timestamp when the project was created.")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "789e0123-e89b-12d3-a456-426614174002",
                "owner_id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Vehicle classification",
                "description": "Annotate urban traffic images indicating the type of vehicle present.",
                "labels": ["car", "truck", "motorcycle", "bicycle"],
                "labelers": [{"id": "456e7890-e89b-12d3-a456-426614174001", "username": "labeler1"}],
            }
        }
    }


class PaginatedProjectResponse(PaginatedResponse[ProjectResponse]):
    """Paginated response containing a list of projects."""

    pass
