"""Pydantic schemas for image-related requests and responses."""

from uuid import UUID

from pydantic import BaseModel, Field

from ulabel.application.import_images_from_storage import ImportJobStatus
from ulabel.domain.images import ImageStatus


class AddImageRequest(BaseModel):
    """Request body for registering an existing storage object as a project image."""
    storage_key: str = Field(
        ...,
        description="Key of an object already present in the storage bucket (MinIO/S3).",
        examples=["raw/image001.jpg"],
    )

    model_config = {
        "json_schema_extra": {"example": {"storage_key": "raw/image001.jpg"}}
    }


class ImageResponse(BaseModel):
    """Response body for an image resource."""

    id: UUID = Field(..., description="Unique image identifier.")
    project_id: UUID = Field(..., description="ID of the project this image belongs to.")
    storage_key: str = Field(..., description="Object key in the storage bucket.")
    status: ImageStatus = Field(
        ...,
        description="Image status: `pending` (available), `in_progress` (assigned), or `done` (labelled).",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "abc12345-e89b-12d3-a456-426614174003",
                "project_id": "789e0123-e89b-12d3-a456-426614174002",
                "storage_key": "789e0123-e89b-12d3-a456-426614174002/abc12345-e89b-12d3-a456-426614174003",
                "status": "pending",
            }
        }
    }


class SubmitLabelRequest(BaseModel):
    """Request body for submitting a label for an assigned image."""

    labeler_id: UUID = Field(
        ...,
        description="ID of the labeler submitting the label.",
    )
    assignment_id: UUID = Field(
        ...,
        description="Assignment ID received when the image was assigned via the `/next` endpoint.",
    )
    label: str = Field(
        ...,
        description="The label to assign to the image. Must be one of the project's allowed labels.",
        examples=["cat"],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "labeler_id": "abc12345-e89b-12d3-a456-426614174001",
                "assignment_id": "def67890-e89b-12d3-a456-426614174004",
                "label": "cat",
            }
        }
    }


class LabelRecordResponse(BaseModel):
    """Response body for a label record."""

    id: UUID = Field(..., description="Unique label record identifier.")
    project_id: UUID = Field(..., description="ID of the project.")
    image_id: UUID = Field(..., description="ID of the labelled image.")
    labeler_id: UUID = Field(..., description="ID of the labeler who submitted the label.")
    label: str = Field(..., description="The assigned label.")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "aaa11111-e89b-12d3-a456-426614174010",
                "project_id": "789e0123-e89b-12d3-a456-426614174002",
                "image_id": "abc12345-e89b-12d3-a456-426614174003",
                "labeler_id": "abc12345-e89b-12d3-a456-426614174001",
                "label": "cat",
            }
        }
    }


class SubmitLabelResponse(BaseModel):
    """Response body for a submitted label, including labeler ranking."""

    id: UUID = Field(..., description="Unique label record identifier.")
    project_id: UUID = Field(..., description="ID of the project.")
    image_id: UUID = Field(..., description="ID of the labelled image.")
    labeler_id: UUID = Field(..., description="ID of the labeler who submitted the label.")
    label: str = Field(..., description="The assigned label.")
    labeler_count: int = Field(..., description="Total number of labels submitted by this labeler in this project.")
    ranking: int = Field(..., description="Labeler's ranking position in this project (1 = most labels).")
    total_labelers: int = Field(..., description="Total number of labelers who have submitted at least one label in this project.")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "aaa11111-e89b-12d3-a456-426614174010",
                "project_id": "789e0123-e89b-12d3-a456-426614174002",
                "image_id": "abc12345-e89b-12d3-a456-426614174003",
                "labeler_id": "abc12345-e89b-12d3-a456-426614174001",
                "label": "cat",
                "labeler_count": 42,
                "ranking": 1,
                "total_labelers": 5,
            }
        }
    }


class ImportImagesRequest(BaseModel):
    """Request body for starting a bulk image import from storage."""

    prefix: str = Field(
        ...,
        description="Bucket path prefix used to filter which objects to import.",
        examples=["raw/batch-01/"],
    )

    model_config = {
        "json_schema_extra": {"example": {"prefix": "raw/batch-01/"}}
    }


class ImportJobResponse(BaseModel):
    """Response body for an import job with its current status."""

    import_id: UUID = Field(..., description="Unique import job identifier. Use it to poll for status.")
    project_id: UUID = Field(..., description="ID of the target project.")
    prefix: str = Field(..., description="Prefix used to filter objects in the bucket.")
    status: ImportJobStatus = Field(..., description="Job status: `running`, `done`, or `failed`.")
    imported: int = Field(..., description="Number of images imported so far.")
    error: str | None = Field(default=None, description="Error message if status is `failed`. `null` otherwise.")

    model_config = {
        "json_schema_extra": {
            "example": {
                "import_id": "fed54321-e89b-12d3-a456-426614174005",
                "project_id": "789e0123-e89b-12d3-a456-426614174002",
                "prefix": "raw/batch-01/",
                "status": "done",
                "imported": 250,
                "error": None,
            }
        }
    }
