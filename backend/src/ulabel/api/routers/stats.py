"""Router for project statistics endpoints.

Provides an endpoint to retrieve labelling statistics for a project,
including image counts, class distribution, and per-labeler activity.
"""

from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from ulabel.api.schemas.stats import (
    DailyCountSchema,
    DailyLabelerTotalSchema,
    DailyTotalSchema,
    LabelerClassCountSchema,
    LabelerDailyActivitySchema,
    ProjectStatsResponse,
)
from ulabel.application.get_project_stats import GetProjectStatsUseCase
from ulabel.container import Container

router = APIRouter()


@router.get(
    "/{project_id}/stats",
    response_model=ProjectStatsResponse,
    summary="Get project statistics",
    description="""
Returns labelling statistics for a project, including total/labeled image counts,
class distribution, per-labeler breakdowns, and daily activity.
""",
    responses={
        404: {
            "description": "Project not found.",
            "content": {"application/json": {"example": {"error": {"code": "PROJECT_NOT_FOUND", "message": "Project not found", "details": []}}}},
        },
    },
)
@inject
async def get_project_stats(
    project_id: UUID,
    use_case: GetProjectStatsUseCase = Depends(Provide[Container.get_project_stats_use_case]),
):
    """Retrieve labelling statistics for a project.

    Args:
        project_id: The project to get statistics for.
        use_case: Injected get-project-stats use case.

    Returns:
        A ProjectStatsResponse with image counts, class distribution,
        per-labeler breakdowns, and daily activity data.
    """
    stats = await use_case.execute(project_id=project_id)

    return ProjectStatsResponse(
        total_images=stats.total_images,
        labeled_images=stats.labeled_images,
        class_distribution=stats.class_distribution,
        labeler_class_counts=[
            LabelerClassCountSchema(
                labeler_id=lc.labeler_id, username=lc.username, counts=lc.counts
            )
            for lc in stats.labeler_class_counts
        ],
        labeler_daily_activity=[
            LabelerDailyActivitySchema(
                labeler_id=la.labeler_id,
                username=la.username,
                daily=[
                    DailyCountSchema(date=d.date, counts=d.counts) for d in la.daily
                ],
            )
            for la in stats.labeler_daily_activity
        ],
        daily_totals=[
            DailyTotalSchema(
                date=dt.date,
                labelers=[
                    DailyLabelerTotalSchema(
                        labeler_id=dl.labeler_id, username=dl.username, count=dl.count
                    )
                    for dl in dt.labelers
                ],
            )
            for dt in stats.daily_totals
        ],
    )
