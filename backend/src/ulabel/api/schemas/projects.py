from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from ulabel.api.schemas.pagination import PaginatedResponse


class CreateProjectRequest(BaseModel):
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
    labeler_id: UUID = Field(..., description="ID of the `labeler` user to add to the project.")

    model_config = {
        "json_schema_extra": {
            "example": {"labeler_id": "456e7890-e89b-12d3-a456-426614174001"}
        }
    }


class ProjectResponse(BaseModel):
    id: UUID = Field(..., description="Unique project identifier.")
    owner_id: UUID = Field(..., description="ID of the admin owner.")
    name: str = Field(..., description="Project name.")
    description: str = Field(..., description="Project description.")
    labels: set[str] = Field(..., description="Labels available in the project.")
    created_at: datetime = Field(..., description="Timestamp when the project was created.")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "789e0123-e89b-12d3-a456-426614174002",
                "owner_id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Vehicle classification",
                "description": "Annotate urban traffic images indicating the type of vehicle present.",
                "labels": ["car", "truck", "motorcycle", "bicycle"],
            }
        }
    }


class PaginatedProjectResponse(PaginatedResponse[ProjectResponse]):
    pass
