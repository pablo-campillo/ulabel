"""Router for image management endpoints.

Provides endpoints for registering, uploading, bulk-importing images,
checking import job status, and submitting labels for images.
"""

from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile, status

from ulabel.api.schemas.images import AddImageRequest, ImageResponse, ImportImagesRequest, ImportJobResponse, SubmitLabelRequest, SubmitLabelResponse
from ulabel.application.add_image_to_project import AddImageToProjectUseCase
from ulabel.application.import_images_from_storage import ImportImagesFromStorageUseCase
from ulabel.application.submit_label import SubmitLabelUseCase
from ulabel.application.upload_image_to_project import UploadImageToProjectUseCase
from ulabel.container import Container

router = APIRouter()


@router.post(
    "/{project_id}/images",
    response_model=ImageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register image by storage key",
    description="""
Registers an image that **already exists** in the storage bucket into the project.
Use this endpoint when images are uploaded to the bucket externally and only need
to be referenced in the project.

To upload an image directly from the client, use `POST /{project_id}/images/upload`.
To bulk-import from a bucket prefix, use `POST /{project_id}/images/import`.
""",
    responses={
        201: {"description": "Image registered with status `pending`."},
        404: {
            "description": "Project not found.",
            "content": {"application/json": {"example": {"error": {"code": "PROJECT_NOT_FOUND", "message": "Project not found", "details": []}}}},
        },
    },
)
@inject
async def add_image(
    project_id: UUID,
    request: AddImageRequest,
    use_case: AddImageToProjectUseCase = Depends(Provide[Container.add_image_to_project_use_case]),
):
    """Register an existing storage object as a project image.

    Args:
        project_id: The target project ID.
        request: Contains the storage key of the existing object.
        use_case: Injected add-image use case.

    Returns:
        An ImageResponse with the registered image details.
    """
    image = await use_case.execute(project_id=project_id, storage_key=request.storage_key)
    return ImageResponse(
        id=image.id,
        project_id=image.project_id,
        storage_key=image.storage_key,
        status=image.status,
    )


@router.post(
    "/{project_id}/images/upload",
    response_model=ImageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload image directly",
    description="""
Uploads an image file to the storage bucket and registers it in the project in a
single step.

The image is stored under the key `{project_id}/{image_id}` and immediately becomes
available for labelers to request.

**Content-Type:** `multipart/form-data` — the form field must be named `file`.
""",
    responses={
        201: {"description": "Image uploaded and registered with status `pending`."},
        404: {
            "description": "Project not found.",
            "content": {"application/json": {"example": {"error": {"code": "PROJECT_NOT_FOUND", "message": "Project not found", "details": []}}}},
        },
    },
)
@inject
async def upload_image(
    project_id: UUID,
    file: UploadFile,
    use_case: UploadImageToProjectUseCase = Depends(Provide[Container.upload_image_to_project_use_case]),
):
    """Upload an image file and register it in the project.

    Args:
        project_id: The target project ID.
        file: The uploaded image file.
        use_case: Injected upload-image use case.

    Returns:
        An ImageResponse with the newly created image details.
    """
    data = await file.read()
    image = await use_case.execute(
        project_id=project_id,
        data=data,
        content_type=file.content_type or "application/octet-stream",
    )
    return ImageResponse(
        id=image.id,
        project_id=image.project_id,
        storage_key=image.storage_key,
        status=image.status,
    )


@router.post(
    "/{project_id}/images/import",
    response_model=ImportJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Bulk import images from storage",
    description="""
Starts an **asynchronous** import job that lists all objects in the bucket under the
given `prefix` and registers them as project images.

The response is returned immediately with `status: "running"`. Use
`GET /{project_id}/images/imports/{import_id}` to poll for progress.

Objects are processed in batches of 1,000. If an error occurs during the import,
the job moves to `status: "failed"` and the `error` field contains the message.
""",
    responses={
        202: {"description": "Import job started. Poll for progress using the returned `import_id`."},
        404: {
            "description": "Project not found.",
            "content": {"application/json": {"example": {"error": {"code": "PROJECT_NOT_FOUND", "message": "Project not found", "details": []}}}},
        },
    },
)
@inject
async def import_images(
    project_id: UUID,
    request: ImportImagesRequest,
    background_tasks: BackgroundTasks,
    use_case: ImportImagesFromStorageUseCase = Depends(Provide[Container.import_images_use_case]),
):
    """Start an asynchronous bulk import of images from a storage prefix.

    Args:
        project_id: The target project ID.
        request: Contains the bucket prefix to import from.
        background_tasks: FastAPI background task manager.
        use_case: Injected import use case.

    Returns:
        An ImportJobResponse with the job ID and initial status.
    """
    job = await use_case.start(project_id=project_id, prefix=request.prefix)
    background_tasks.add_task(use_case.run, job)
    return ImportJobResponse(
        import_id=job.id,
        project_id=job.project_id,
        prefix=job.prefix,
        status=job.status,
        imported=job.imported,
    )


@router.get(
    "/{project_id}/images/imports/{import_id}",
    response_model=ImportJobResponse,
    summary="Get import job status",
    description="""
Returns the current state of an import job previously started with
`POST /{project_id}/images/import`.

Possible `status` values:
- `running` — the import is still in progress.
- `done` — all images under the prefix have been imported.
- `failed` — an error occurred; check the `error` field for details.
""",
    responses={
        200: {"description": "Current import job state."},
        404: {
            "description": "Import job not found or does not belong to the given project.",
            "content": {"application/json": {"example": {"error": {"code": "IMPORT_JOB_NOT_FOUND", "message": "Import job not found", "details": []}}}},
        },
    },
)
@inject
async def get_import_status(
    project_id: UUID,
    import_id: UUID,
    use_case: ImportImagesFromStorageUseCase = Depends(Provide[Container.import_images_use_case]),
):
    """Retrieve the current status of a bulk import job.

    Args:
        project_id: The project the import belongs to.
        import_id: The import job identifier.
        use_case: Injected import use case.

    Returns:
        An ImportJobResponse with the current job state.
    """
    job = use_case.get_job(import_id, project_id)
    return ImportJobResponse(
        import_id=job.id,
        project_id=job.project_id,
        prefix=job.prefix,
        status=job.status,
        imported=job.imported,
        error=job.error,
    )


@router.post(
    "/{project_id}/images/{image_id}/label",
    response_model=SubmitLabelResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit label for an image",
    description="""
Submits a label for an image that is currently assigned (`in_progress`) to the labeler.

The `assignment_id` must match the one returned by `POST /{project_id}/assignments` to
prevent stale or duplicate submissions. The `label` must be one of the labels configured
for the project.

On success the image transitions to `done` and cannot be re-assigned.
""",
    responses={
        201: {"description": "Label recorded and image marked as `done`."},
        403: {
            "description": "The labeler does not match the assigned labeler.",
            "content": {"application/json": {"example": {"error": {"code": "LABELER_MISMATCH", "message": "Labeler mismatch", "details": []}}}},
        },
        404: {
            "description": "Project or image not found.",
            "content": {"application/json": {"example": {"error": {"code": "IMAGE_NOT_FOUND", "message": "Image not found", "details": []}}}},
        },
        409: {
            "description": "Image is not in progress or assignment ID does not match.",
            "content": {"application/json": {"example": {"error": {"code": "IMAGE_NOT_IN_PROGRESS", "message": "Image is not in progress", "details": []}}}},
        },
        422: {
            "description": "Label is not valid for this project.",
            "content": {"application/json": {"example": {"error": {"code": "INVALID_LABEL", "message": "Invalid label", "details": []}}}},
        },
    },
)
@inject
async def submit_label(
    project_id: UUID,
    image_id: UUID,
    request: SubmitLabelRequest,
    use_case: SubmitLabelUseCase = Depends(Provide[Container.submit_label_use_case]),
):
    """Submit a label for an assigned image.

    Args:
        project_id: The project the image belongs to.
        image_id: The image to label.
        request: Contains labeler ID, assignment ID, and the label value.
        use_case: Injected submit-label use case.

    Returns:
        A SubmitLabelResponse with the label record and labeler ranking.
    """
    label_record, stats = await use_case.execute(
        project_id=project_id,
        image_id=image_id,
        labeler_id=request.labeler_id,
        assignment_id=request.assignment_id,
        label=request.label,
    )
    return SubmitLabelResponse(
        id=label_record.id,
        project_id=label_record.project_id,
        image_id=label_record.image_id,
        labeler_id=label_record.labeler_id,
        label=label_record.label,
        labeler_count=stats.labeler_count,
        ranking=stats.ranking,
        total_labelers=stats.total_labelers,
    )
