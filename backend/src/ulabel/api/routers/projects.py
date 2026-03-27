from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status

from ulabel.api.schemas.projects import AddLabelerRequest, CreateProjectRequest, ProjectResponse
from ulabel.application.add_labeler_to_project import AddLabelerToProjectUseCase, ProjectNotFound
from ulabel.application.create_project import CreateProjectUseCase, Unauthorized
from ulabel.application.login import UserNotFound
from ulabel.container import Container

router = APIRouter()


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create project",
    description="""
Creates a new labelling project. The `owner_id` field must reference a user with the
`admin` role; otherwise a 403 error is returned.

The `labels` set defines all annotation options available to labelers and cannot be
changed after the project is created.
""",
    responses={
        201: {"description": "Project created successfully."},
        403: {
            "description": "The specified owner does not have the `admin` role.",
            "content": {"application/json": {"example": {"detail": "Owner is not an admin"}}},
        },
        404: {
            "description": "No user found with the given `owner_id`.",
            "content": {"application/json": {"example": {"detail": "Owner not found"}}},
        },
    },
)
@inject
async def create_project(
    request: CreateProjectRequest,
    use_case: CreateProjectUseCase = Depends(Provide[Container.create_project_use_case]),
):
    try:
        project = await use_case.execute(
            owner_id=request.owner_id,
            name=request.name,
            description=request.description,
            labels=request.labels,
        )
    except UserNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner not found")
    except Unauthorized:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner is not an admin")
    return ProjectResponse(
        id=project.id,
        owner_id=project.owner.id,
        name=project.name,
        description=project.description,
        labels=project.labels,
        created_at=project.created_at,
    )


@router.post(
    "/{project_id}/labelers",
    response_model=ProjectResponse,
    summary="Add labeler to project",
    description="""
Assigns a user with the `labeler` role to an existing project. From that point on,
the labeler can see the project in their list and request pending images.

The user referenced by `labeler_id` must exist and have the `labeler` role; otherwise
a 403 is returned.
""",
    responses={
        200: {"description": "Labeler added. Returns the updated project."},
        403: {
            "description": "The specified user does not have the `labeler` role.",
            "content": {"application/json": {"example": {"detail": "User is not a labeler"}}},
        },
        404: {
            "description": "Project or labeler not found.",
            "content": {
                "application/json": {
                    "examples": {
                        "project_not_found": {"value": {"detail": "Project not found"}},
                        "labeler_not_found": {"value": {"detail": "Labeler not found"}},
                    }
                }
            },
        },
    },
)
@inject
async def add_labeler(
    project_id: UUID,
    request: AddLabelerRequest,
    use_case: AddLabelerToProjectUseCase = Depends(Provide[Container.add_labeler_to_project_use_case]),
):
    try:
        project = await use_case.execute(project_id=project_id, labeler_id=request.labeler_id)
    except ProjectNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    except UserNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Labeler not found")
    except Unauthorized:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not a labeler")
    return ProjectResponse(
        id=project.id,
        owner_id=project.owner.id,
        name=project.name,
        description=project.description,
        labels=project.labels,
        created_at=project.created_at,
    )
