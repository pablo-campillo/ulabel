from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Query, status

from ulabel.api.schemas.projects import (
    AddLabelerRequest,
    CreateProjectRequest,
    LabelerInfo,
    PaginatedProjectResponse,
    ProjectResponse,
    UpdateProjectRequest,
)
from ulabel.application.add_labeler_to_project import AddLabelerToProjectUseCase, ProjectNotFound
from ulabel.application.create_project import CreateProjectUseCase, Unauthorized
from ulabel.application.list_projects import ListProjectsUseCase
from ulabel.application.login import UserNotFound
from ulabel.application.update_project import UpdateProjectUseCase
from ulabel.container import Container
from ulabel.domain.projects import Project
from ulabel.domain.ports.user_repository import UserRepository

router = APIRouter()


async def _resolve_labelers(project: Project, user_repo: UserRepository) -> list[LabelerInfo]:
    labelers: list[LabelerInfo] = []
    for lid in project.labeler_ids:
        user = await user_repo.get_by_id(lid)
        if user:
            labelers.append(LabelerInfo(id=user.id, username=user.username))
        else:
            labelers.append(LabelerInfo(id=lid, username=str(lid)))
    return labelers


async def _to_response(project: Project, user_repo: UserRepository) -> ProjectResponse:
    labelers = await _resolve_labelers(project, user_repo)
    return ProjectResponse(
        id=project.id,
        owner_id=project.owner.id,
        name=project.name,
        description=project.description,
        labels=project.labels,
        labelers=labelers,
        created_at=project.created_at,
    )


@router.get(
    "",
    response_model=PaginatedProjectResponse,
    summary="List all projects",
    description="Returns a paginated list of all projects, ordered by creation date (newest first).",
    responses={200: {"description": "Paginated list of projects."}},
)
@inject
async def list_projects(
    limit: int = Query(default=20, ge=1, le=100, description="Max items per page."),
    offset: int = Query(default=0, ge=0, description="Number of items to skip."),
    use_case: ListProjectsUseCase = Depends(Provide[Container.list_projects_use_case]),
    user_repo: UserRepository = Depends(Provide[Container.user_repository]),
):
    result = await use_case.execute(limit=limit, offset=offset)
    items = [await _to_response(p, user_repo) for p in result.items]
    return PaginatedProjectResponse(
        items=items,
        total=result.total,
        limit=limit,
        offset=offset,
    )


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
    user_repo: UserRepository = Depends(Provide[Container.user_repository]),
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
    return await _to_response(project, user_repo)


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update project",
    description="""
Updates a project's name, description, and/or labeler assignments.

Only the fields present in the request body are modified. Omitted fields remain
unchanged. When `labeler_ids` is provided, it **replaces** the full set of
assigned labelers — every ID must reference an existing user with the `labeler`
role.
""",
    responses={
        200: {"description": "Project updated successfully."},
        403: {
            "description": "One of the provided labeler IDs does not have the `labeler` role.",
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
async def update_project(
    project_id: UUID,
    request: UpdateProjectRequest,
    use_case: UpdateProjectUseCase = Depends(Provide[Container.update_project_use_case]),
    user_repo: UserRepository = Depends(Provide[Container.user_repository]),
):
    try:
        project = await use_case.execute(
            project_id=project_id,
            name=request.name,
            description=request.description,
            labeler_ids=set(request.labeler_ids) if request.labeler_ids is not None else None,
        )
    except ProjectNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    except UserNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Labeler not found")
    except Unauthorized:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not a labeler")
    return await _to_response(project, user_repo)


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
    user_repo: UserRepository = Depends(Provide[Container.user_repository]),
):
    try:
        project = await use_case.execute(project_id=project_id, labeler_id=request.labeler_id)
    except ProjectNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    except UserNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Labeler not found")
    except Unauthorized:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not a labeler")
    return await _to_response(project, user_repo)
