from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, status

from ulabel.api.schemas.images import AddImageRequest, ImageResponse, ImportImagesRequest, ImportJobResponse, SubmitLabelRequest, SubmitLabelResponse
from ulabel.application.add_image_to_project import AddImageToProjectUseCase
from ulabel.application.add_labeler_to_project import ProjectNotFound
from ulabel.application.import_images_from_storage import ImportImagesFromStorageUseCase
from ulabel.application.submit_label import AssignmentMismatch, ImageNotFound, ImageNotInProgress, InvalidLabel, LabelerMismatch, SubmitLabelUseCase
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
            "content": {"application/json": {"example": {"detail": "Project not found"}}},
        },
    },
)
@inject
async def add_image(
    project_id: UUID,
    request: AddImageRequest,
    use_case: AddImageToProjectUseCase = Depends(Provide[Container.add_image_to_project_use_case]),
):
    try:
        image = await use_case.execute(project_id=project_id, storage_key=request.storage_key)
    except ProjectNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
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
            "content": {"application/json": {"example": {"detail": "Project not found"}}},
        },
    },
)
@inject
async def upload_image(
    project_id: UUID,
    file: UploadFile,
    use_case: UploadImageToProjectUseCase = Depends(Provide[Container.upload_image_to_project_use_case]),
):
    data = await file.read()
    try:
        image = await use_case.execute(
            project_id=project_id,
            data=data,
            content_type=file.content_type or "application/octet-stream",
        )
    except ProjectNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
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
            "content": {"application/json": {"example": {"detail": "Project not found"}}},
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
    try:
        job = await use_case.start(project_id=project_id, prefix=request.prefix)
    except ProjectNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
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
            "content": {"application/json": {"example": {"detail": "Import job not found"}}},
        },
    },
)
@inject
async def get_import_status(
    project_id: UUID,
    import_id: UUID,
    use_case: ImportImagesFromStorageUseCase = Depends(Provide[Container.import_images_use_case]),
):
    job = use_case.get_job(import_id)
    if job is None or job.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import job not found")
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
            "content": {"application/json": {"example": {"detail": "Labeler mismatch"}}},
        },
        404: {
            "description": "Project or image not found.",
            "content": {"application/json": {"example": {"detail": "Image not found"}}},
        },
        409: {
            "description": "Image is not in progress or assignment ID does not match.",
            "content": {"application/json": {"example": {"detail": "Image is not in progress"}}},
        },
        422: {
            "description": "Label is not valid for this project.",
            "content": {"application/json": {"example": {"detail": "Invalid label"}}},
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
    try:
        label_record, stats = await use_case.execute(
            project_id=project_id,
            image_id=image_id,
            labeler_id=request.labeler_id,
            assignment_id=request.assignment_id,
            label=request.label,
        )
    except ProjectNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    except ImageNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    except ImageNotInProgress:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Image is not in progress")
    except AssignmentMismatch:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Assignment ID mismatch")
    except LabelerMismatch:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Labeler mismatch")
    except InvalidLabel:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Invalid label"
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
