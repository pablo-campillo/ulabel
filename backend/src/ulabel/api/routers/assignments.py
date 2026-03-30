"""Router for image assignment endpoints.

Handles creating assignments that pair labelers with pending images
and generate time-limited presigned URLs for image access.
"""

import logging
from datetime import timedelta
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status

from ulabel.api.schemas.assignments import AssignmentResponse, CreateAssignmentRequest
from ulabel.application.create_assignment import CreateAssignmentUseCase
from ulabel.container import Container
from ulabel.domain.ports.storage_service import StorageService

logger = logging.getLogger(__name__)

router = APIRouter()

ASSIGNMENT_TIMEOUT = timedelta(minutes=30)


@router.post(
    "/{project_id}/assignments",
    response_model=AssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create image assignment",
    description="""
Assigns the next `pending` image in the project to the given labeler.

The image transitions to `in_progress` and a **presigned URL** valid for 30 minutes
is generated for direct file access from the browser or client.

If the labeler does not complete the task before the time expires, the image is
automatically reset to `pending` and becomes available for another labeler.

**Special responses:**
- `204 No Content` — no pending images in this project right now.
- `403 Forbidden` — the labeler is not assigned to this project.
""",
    responses={
        201: {"description": "Assignment created. Includes a presigned URL for file access."},
        204: {"description": "No pending images available in the project right now."},
        403: {
            "description": "The labeler does not belong to this project.",
            "content": {"application/json": {"example": {"error": {"code": "LABELER_NOT_IN_PROJECT", "message": "Labeler is not in this project", "details": []}}}},
        },
        404: {
            "description": "Project not found.",
            "content": {"application/json": {"example": {"error": {"code": "PROJECT_NOT_FOUND", "message": "Project not found", "details": []}}}},
        },
    },
)
@inject
async def create_assignment(
    project_id: UUID,
    request: CreateAssignmentRequest,
    use_case: CreateAssignmentUseCase = Depends(Provide[Container.create_assignment_use_case]),
    storage: StorageService = Depends(Provide[Container.storage_service]),
):
    """Assign the next pending image to a labeler and return a presigned URL.

    Args:
        project_id: The project to assign an image from.
        request: Contains the labeler ID to assign the image to.
        use_case: Injected assignment use case.
        storage: Injected storage service for presigned URL generation.

    Returns:
        An AssignmentResponse with image details and a presigned URL.
    """
    image = await use_case.execute(project_id=project_id, labeler_id=request.labeler_id)
    presigned_url = await storage.get_presigned_url(image.storage_key, expires_in=ASSIGNMENT_TIMEOUT)
    logger.info("Assignment created: project=%s image=%s labeler=%s", project_id, image.id, request.labeler_id)
    return AssignmentResponse(
        id=image.id,
        project_id=image.project_id,
        status=image.status,
        assignment_id=image.assignment_id,
        presigned_url=presigned_url,
        presigned_url_expires_in=int(ASSIGNMENT_TIMEOUT.total_seconds()),
    )
