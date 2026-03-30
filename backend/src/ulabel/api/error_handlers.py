"""Centralized error handling for domain exceptions.

Maps domain-layer exceptions to HTTP status codes and structured JSON
error responses, and records domain error metrics.
"""

import logging

from fastapi import Request
from starlette.responses import JSONResponse, Response

from ulabel.application.add_labeler_to_project import ProjectNotFound, UserNotFound
from ulabel.application.create_assignment import LabelerNotInProject, NoImageAvailable
from ulabel.application.create_project import ProjectNameAlreadyExists, Unauthorized
from ulabel.application.export_labels import NoLabelsFound
from ulabel.application.import_images_from_storage import ImportJobNotFound
from ulabel.application.submit_label import (
    AssignmentMismatch,
    ImageNotFound,
    ImageNotInProgress,
    InvalidLabel,
    LabelerMismatch,
)
from ulabel.domain.errors import DomainError
from ulabel.infrastructure.observability.metrics import DOMAIN_ERRORS_TOTAL

EXCEPTION_MAP: dict[type[DomainError], tuple[int, str, str]] = {
    ProjectNotFound: (404, "PROJECT_NOT_FOUND", "Project not found"),
    UserNotFound: (404, "USER_NOT_FOUND", "User not found"),
    Unauthorized: (403, "UNAUTHORIZED", "Unauthorized"),
    ProjectNameAlreadyExists: (409, "PROJECT_NAME_ALREADY_EXISTS", "Project name already exists"),
    LabelerNotInProject: (403, "LABELER_NOT_IN_PROJECT", "Labeler is not in this project"),
    NoImageAvailable: (204, "", ""),
    ImageNotFound: (404, "IMAGE_NOT_FOUND", "Image not found"),
    ImageNotInProgress: (409, "IMAGE_NOT_IN_PROGRESS", "Image is not in progress"),
    AssignmentMismatch: (409, "ASSIGNMENT_MISMATCH", "Assignment ID mismatch"),
    LabelerMismatch: (403, "LABELER_MISMATCH", "Labeler mismatch"),
    InvalidLabel: (422, "INVALID_LABEL", "Invalid label"),
    NoLabelsFound: (404, "NO_LABELS_FOUND", "No labels to export"),
    ImportJobNotFound: (404, "IMPORT_JOB_NOT_FOUND", "Import job not found"),
}


logger = logging.getLogger(__name__)


async def domain_error_handler(request: Request, exc: DomainError) -> Response:
    """Handle domain errors and convert them to appropriate HTTP responses.

    Looks up the exception type in ``EXCEPTION_MAP`` to determine the HTTP
    status code and error code. Logs the error and increments the domain
    error counter metric.

    Args:
        request: The incoming HTTP request.
        exc: The domain error that was raised.

    Returns:
        A JSON response with the error details, or a 204 empty response.
    """
    status_code, code, default_msg = EXCEPTION_MAP[type(exc)]
    if status_code == 204:
        return Response(status_code=204)
    message = str(exc) if str(exc) else default_msg
    logger.warning("Domain error: %s %s %s", code, request.method, request.url.path)
    DOMAIN_ERRORS_TOTAL.labels(code=code, status=status_code).inc()
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "details": []}},
    )
