from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status

from ulabel.api.schemas.projects import ProjectResponse
from ulabel.application.create_project import Unauthorized
from ulabel.application.get_labeler_projects import GetLabelerProjectsUseCase
from ulabel.application.login import UserNotFound
from ulabel.container import Container

router = APIRouter()


@router.get(
    "/{labeler_id}/projects",
    response_model=list[ProjectResponse],
    summary="List labeler projects",
    description="""
Returns all projects the labeler is assigned to.

The user must exist and have the `labeler` role. If the user exists but has the
`admin` role, a 403 is returned.

Use this response to show the labeler which projects they can work on and which
labels are available in each one.
""",
    responses={
        200: {"description": "List of projects assigned to the labeler."},
        403: {
            "description": "The user does not have the `labeler` role.",
            "content": {"application/json": {"example": {"detail": "User is not a labeler"}}},
        },
        404: {
            "description": "Labeler not found.",
            "content": {"application/json": {"example": {"detail": "Labeler not found"}}},
        },
    },
)
@inject
async def get_labeler_projects(
    labeler_id: UUID,
    use_case: GetLabelerProjectsUseCase = Depends(Provide[Container.get_labeler_projects_use_case]),
):
    try:
        projects = await use_case.execute(labeler_id=labeler_id)
    except UserNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Labeler not found")
    except Unauthorized:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not a labeler")
    return [
        ProjectResponse(
            id=p.id,
            owner_id=p.owner.id,
            name=p.name,
            description=p.description,
            labels=p.labels,
        )
        for p in projects
    ]
