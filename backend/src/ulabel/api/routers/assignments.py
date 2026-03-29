from datetime import timedelta
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status

from ulabel.api.schemas.assignments import AssignmentResponse, CreateAssignmentRequest
from ulabel.application.add_labeler_to_project import ProjectNotFound
from ulabel.application.create_assignment import CreateAssignmentUseCase, LabelerNotInProject, NoImageAvailable
from ulabel.container import Container
from ulabel.domain.ports.storage_service import StorageService

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
            "content": {"application/json": {"example": {"detail": "Labeler is not in this project"}}},
        },
        404: {
            "description": "Project not found.",
            "content": {"application/json": {"example": {"detail": "Project not found"}}},
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
    try:
        image = await use_case.execute(project_id=project_id, labeler_id=request.labeler_id)
    except ProjectNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    except LabelerNotInProject:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Labeler is not in this project")
    except NoImageAvailable:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)
    presigned_url = await storage.get_presigned_url(image.storage_key, expires_in=ASSIGNMENT_TIMEOUT)
    return AssignmentResponse(
        id=image.id,
        project_id=image.project_id,
        status=image.status,
        assignment_id=image.assignment_id,
        presigned_url=presigned_url,
        presigned_url_expires_in=int(ASSIGNMENT_TIMEOUT.total_seconds()),
    )
