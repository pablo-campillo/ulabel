from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import RedirectResponse

from ulabel.application.export_labels import ExportFormat, ExportLabelsUseCase
from ulabel.container import Container

router = APIRouter()


@router.get(
    "/{project_id}/export",
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    summary="Export label data",
    description="""
Exports all label records for the project as a downloadable file.

The response is a **307 redirect** to a presigned MinIO URL where the file can be
downloaded directly. The file is cached; subsequent requests on the same day return
the cached version unless new labels have been submitted.
""",
    responses={
        307: {"description": "Redirect to presigned download URL."},
        404: {
            "description": "Project not found or no labels exist yet.",
            "content": {"application/json": {"example": {"error": {"code": "PROJECT_NOT_FOUND", "message": "Project not found", "details": []}}}},
        },
    },
)
@inject
async def export_labels(
    project_id: UUID,
    fmt: ExportFormat = Query(default=ExportFormat.JSON, alias="format"),
    use_case: ExportLabelsUseCase = Depends(Provide[Container.export_labels_use_case]),
) -> RedirectResponse:
    presigned_url = await use_case.execute(project_id=project_id, fmt=fmt)
    return RedirectResponse(url=presigned_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
