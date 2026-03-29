from uuid import UUID

from pydantic import BaseModel, Field

from ulabel.domain.images import ImageStatus


class CreateAssignmentRequest(BaseModel):
    labeler_id: UUID = Field(
        ...,
        description="ID of the labeler to assign the next pending image to.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {"labeler_id": "abc12345-e89b-12d3-a456-426614174001"}
        }
    }


class AssignmentResponse(BaseModel):
    id: UUID = Field(..., description="Unique image identifier.")
    project_id: UUID = Field(..., description="ID of the project this image belongs to.")
    status: ImageStatus = Field(..., description="Current image status (always `in_progress` in this response).")
    assignment_id: UUID = Field(
        ...,
        description="Unique ID for this assignment. Use it to track the labelling session.",
    )
    presigned_url: str = Field(
        ...,
        description="Time-limited URL for direct access to the image file from the browser or client.",
    )
    presigned_url_expires_in: int = Field(
        ...,
        description="Seconds until the URL and the assignment expire (default 1800 s = 30 min). After that, the image reverts to `pending`.",
        examples=[1800],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "abc12345-e89b-12d3-a456-426614174003",
                "project_id": "789e0123-e89b-12d3-a456-426614174002",
                "status": "in_progress",
                "assignment_id": "def67890-e89b-12d3-a456-426614174004",
                "presigned_url": "https://storage.example.com/ulabel/project/image?X-Amz-Expires=1800&X-Amz-Signature=...",
                "presigned_url_expires_in": 1800,
            }
        }
    }
