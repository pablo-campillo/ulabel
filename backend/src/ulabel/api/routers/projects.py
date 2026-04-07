"""Router for project management endpoints.

Provides CRUD operations for labelling projects, including creation,
listing with pagination, detail retrieval, updating, and adding labelers.
"""

import logging
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, status

from ulabel.api.schemas.projects import (
    AddLabelerRequest,
    CreateProjectRequest,
    LabelerInfo,
    PaginatedProjectSummaryResponse,
    ProjectDetail,
    ProjectSummary,
    UpdateProjectRequest,
)
from ulabel.application.add_labeler_to_project import AddLabelerToProjectUseCase
from ulabel.application.create_project import CreateProjectUseCase
from ulabel.application.dtos import ProjectWithLabelers
from ulabel.application.get_project import GetProjectUseCase
from ulabel.application.list_projects import ListProjectsUseCase
from ulabel.application.update_project import UpdateProjectUseCase
from ulabel.container import Container
from ulabel.domain.projects import Project

logger = logging.getLogger(__name__)

router = APIRouter()


def _to_summary(project: Project) -> ProjectSummary:
    """Convert a domain Project to a ProjectSummary."""
    return ProjectSummary(
        id=project.id,
        owner_id=project.owner.id,
        name=project.name,
        description=project.description,
        labels=project.labels,
        labeler_count=len(project.labeler_ids),
        created_at=project.created_at,
    )


def _to_detail(result: ProjectWithLabelers) -> ProjectDetail:
    """Convert a ProjectWithLabelers DTO to a ProjectDetail response."""
    return ProjectDetail(
        id=result.project.id,
        owner_id=result.project.owner.id,
        name=result.project.name,
        description=result.project.description,
        labels=result.project.labels,
        labelers=[LabelerInfo(id=lab.id, username=lab.username) for lab in result.labelers],
        created_at=result.project.created_at,
    )


@router.get(
    "",
    response_model=PaginatedProjectSummaryResponse,
    summary="List all projects",
    description=(
        "Returns a paginated list of all projects, ordered by creation date (newest first)."
    ),
    responses={200: {"description": "Paginated list of projects."}},
)
@inject
async def list_projects(
    limit: int = Query(default=20, ge=1, le=100, description="Max items per page."),
    offset: int = Query(default=0, ge=0, description="Number of items to skip."),
    name: str | None = Query(
        default=None,
        description="Filter projects by name (case-insensitive, contains match).",
    ),
    use_case: ListProjectsUseCase = Depends(Provide[Container.list_projects_use_case]),
) -> PaginatedProjectSummaryResponse:
    """List all projects with pagination and optional name filtering.

    Args:
        limit: Maximum number of items per page.
        offset: Number of items to skip.
        name: Optional name filter (case-insensitive contains match).
        use_case: Injected list-projects use case.

    Returns:
        A PaginatedProjectSummaryResponse with project summaries and total count.
    """
    result = await use_case.execute(limit=limit, offset=offset, name=name)
    items = [_to_summary(p) for p in result.items]
    return PaginatedProjectSummaryResponse(
        items=items,
        total=result.total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{project_id}",
    response_model=ProjectDetail,
    summary="Get project detail",
    description=("Returns a single project with fully resolved labeler information."),
    responses={
        200: {"description": "Project detail with resolved labelers."},
        404: {
            "description": "Project not found.",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "PROJECT_NOT_FOUND",
                            "message": "Project not found",
                            "details": [],
                        }
                    }
                }
            },
        },
    },
)
@inject
async def get_project(
    project_id: UUID,
    use_case: GetProjectUseCase = Depends(Provide[Container.get_project_use_case]),
) -> ProjectDetail:
    """Retrieve a single project with resolved labeler details.

    Args:
        project_id: The project's unique identifier.
        use_case: Injected get-project use case.

    Returns:
        A ProjectDetail with resolved labeler usernames.
    """
    result = await use_case.execute(project_id=project_id)
    return _to_detail(result)


@router.post(
    "",
    response_model=ProjectDetail,
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
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "UNAUTHORIZED",
                            "message": "Owner is not an admin",
                            "details": [],
                        }
                    }
                }
            },
        },
        404: {
            "description": "No user found with the given `owner_id`.",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "USER_NOT_FOUND",
                            "message": "Owner not found",
                            "details": [],
                        }
                    }
                }
            },
        },
        409: {
            "description": "A project with the same name already exists.",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "PROJECT_NAME_ALREADY_EXISTS",
                            "message": "Project name already exists",
                            "details": [],
                        }
                    }
                }
            },
        },
    },
)
@inject
async def create_project(
    request: CreateProjectRequest,
    use_case: CreateProjectUseCase = Depends(Provide[Container.create_project_use_case]),
    get_project_use_case: GetProjectUseCase = Depends(Provide[Container.get_project_use_case]),
) -> ProjectDetail:
    """Create a new labelling project.

    Args:
        request: Project creation parameters including owner, name, and labels.
        use_case: Injected create-project use case.
        get_project_use_case: Injected get-project use case for response building.

    Returns:
        A ProjectDetail with the newly created project details.
    """
    project = await use_case.execute(
        owner_id=request.owner_id,
        name=request.name,
        description=request.description,
        labels=request.labels,
    )
    logger.info(
        "Project created: id=%s name=%s owner=%s labels=%d",
        project.id,
        request.name,
        request.owner_id,
        len(request.labels),
    )
    result = await get_project_use_case.execute(project_id=project.id)
    return _to_detail(result)


@router.patch(
    "/{project_id}",
    response_model=ProjectDetail,
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
            "description": ("One of the provided labeler IDs does not have the `labeler` role."),
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "UNAUTHORIZED",
                            "message": "User is not a labeler",
                            "details": [],
                        }
                    }
                }
            },
        },
        404: {
            "description": "Project or labeler not found.",
            "content": {
                "application/json": {
                    "examples": {
                        "project_not_found": {
                            "value": {
                                "error": {
                                    "code": "PROJECT_NOT_FOUND",
                                    "message": "Project not found",
                                    "details": [],
                                }
                            }
                        },
                        "labeler_not_found": {
                            "value": {
                                "error": {
                                    "code": "USER_NOT_FOUND",
                                    "message": "Labeler not found",
                                    "details": [],
                                }
                            }
                        },
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
    get_project_use_case: GetProjectUseCase = Depends(Provide[Container.get_project_use_case]),
) -> ProjectDetail:
    """Update a project's name, description, or labeler assignments.

    Args:
        project_id: The project to update.
        request: Fields to update (only provided fields are modified).
        use_case: Injected update-project use case.
        get_project_use_case: Injected get-project use case for response building.

    Returns:
        A ProjectDetail with the updated project details.
    """
    await use_case.execute(
        project_id=project_id,
        name=request.name,
        description=request.description,
        labeler_ids=set(request.labeler_ids) if request.labeler_ids is not None else None,
    )
    logger.info("Project updated: id=%s", project_id)
    result = await get_project_use_case.execute(project_id=project_id)
    return _to_detail(result)


@router.post(
    "/{project_id}/labelers",
    response_model=ProjectDetail,
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
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "UNAUTHORIZED",
                            "message": "User is not a labeler",
                            "details": [],
                        }
                    }
                }
            },
        },
        404: {
            "description": "Project or labeler not found.",
            "content": {
                "application/json": {
                    "examples": {
                        "project_not_found": {
                            "value": {
                                "error": {
                                    "code": "PROJECT_NOT_FOUND",
                                    "message": "Project not found",
                                    "details": [],
                                }
                            }
                        },
                        "labeler_not_found": {
                            "value": {
                                "error": {
                                    "code": "USER_NOT_FOUND",
                                    "message": "Labeler not found",
                                    "details": [],
                                }
                            }
                        },
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
    use_case: AddLabelerToProjectUseCase = Depends(
        Provide[Container.add_labeler_to_project_use_case]
    ),
    get_project_use_case: GetProjectUseCase = Depends(Provide[Container.get_project_use_case]),
) -> ProjectDetail:
    """Add a labeler to an existing project.

    Args:
        project_id: The project to add the labeler to.
        request: Contains the labeler user ID.
        use_case: Injected add-labeler use case.
        get_project_use_case: Injected get-project use case for response building.

    Returns:
        A ProjectDetail with the updated project details.
    """
    await use_case.execute(project_id=project_id, labeler_id=request.labeler_id)
    logger.info("Labeler added to project: project=%s labeler=%s", project_id, request.labeler_id)
    result = await get_project_use_case.execute(project_id=project_id)
    return _to_detail(result)
