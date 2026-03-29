from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from ulabel.api.schemas.projects import ProjectResponse
from ulabel.application.get_labeler_projects import GetLabelerProjectsUseCase
from ulabel.application.search_labelers import SearchLabelersUseCase
from ulabel.container import Container

router = APIRouter()


class LabelerAutocompleteItem(BaseModel):
    id: UUID
    username: str


@router.get(
    "/autocomplete",
    response_model=list[LabelerAutocompleteItem],
    summary="Autocomplete labeler usernames",
    description="Search labelers by username prefix. Returns up to `limit` matches.",
)
@inject
async def autocomplete_labelers(
    q: str = Query(min_length=1, description="Username prefix to search for"),
    limit: int = Query(default=10, ge=1, le=50),
    use_case: SearchLabelersUseCase = Depends(Provide[Container.search_labelers_use_case]),
):
    results = await use_case.execute(prefix=q, limit=limit)
    return [LabelerAutocompleteItem(id=u.id, username=u.username) for u in results]


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
            "content": {"application/json": {"example": {"error": {"code": "UNAUTHORIZED", "message": "User is not a labeler", "details": []}}}},
        },
        404: {
            "description": "Labeler not found.",
            "content": {"application/json": {"example": {"error": {"code": "USER_NOT_FOUND", "message": "Labeler not found", "details": []}}}},
        },
    },
)
@inject
async def get_labeler_projects(
    labeler_id: UUID,
    use_case: GetLabelerProjectsUseCase = Depends(Provide[Container.get_labeler_projects_use_case]),
):
    projects = await use_case.execute(labeler_id=labeler_id)
    return [
        ProjectResponse(
            id=p.id,
            owner_id=p.owner.id,
            name=p.name,
            description=p.description,
            labels=p.labels,
            created_at=p.created_at,
        )
        for p in projects
    ]
