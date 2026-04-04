"""FastAPI application entry point for the uLabel API.

Configures the FastAPI app with middleware, error handlers, routers,
and manages the application lifecycle including background tasks.
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from ulabel.api.api import api_router
from ulabel.api.error_handlers import domain_error_handler
from ulabel.container import Container
from ulabel.domain.errors import DomainError
from ulabel.infrastructure.observability.metrics import PrometheusMiddleware, metrics_route
from ulabel.infrastructure.observability.tracing import instrument_fastapi, instrument_libraries, shutdown_tracing

container = Container()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown lifecycle.

    On startup, initializes logging, tracing, storage, and starts the
    background task that expires stale image assignments. On shutdown,
    cancels the background task and shuts down tracing.

    Args:
        app: The FastAPI application instance.

    Yields:
        Control to the running application.
    """
    container.logging_setup.init()
    container.tracer_provider.init()
    instrument_libraries(container.engine())
    await container.storage_service().ensure_bucket()
    task = asyncio.create_task(container.expire_images_task().run())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    shutdown_tracing(container.tracer_provider())


app = FastAPI(
    title="uLabel API",
    description="""
API for managing image labelling projects.

## Workflow

1. **Authentication** — the user calls `POST /v1/token` with their username and receives their ID and role.
2. **Admin** creates projects (`POST /v1/projects`) and adds labelers (`POST /v1/projects/{id}/labelers`).
3. **Image loading** — the admin uploads images one by one (`POST /v1/projects/{id}/images/upload`), registers them by storage key (`POST /v1/projects/{id}/images`), or bulk-imports from the bucket (`POST /v1/projects/{id}/images/import`).
4. **Labelling** — the labeler creates an assignment (`POST /v1/projects/{id}/assignments`), which returns the next pending image with a presigned URL whose expiry is configured via `tasks.image_assignment_timeout_seconds` in `config.yml`. If not completed in time, the assignment expires and the image becomes available again.

## Roles

| Role | Permissions |
|------|-------------|
| `admin` | Create projects, add labelers, upload/import images |
| `labeler` | View their projects, fetch images to label |
""",
    version="1.0.0",
    lifespan=lifespan,
)
app.container = container
app.add_middleware(PrometheusMiddleware)
instrument_fastapi(app)
app.add_exception_handler(DomainError, domain_error_handler)

app.include_router(api_router, prefix="/v1")
app.add_route("/metrics", metrics_route)


@app.get("/", tags=["Health"], summary="Health check", description="Verifies the service is up and running.")
async def root():
    """Return a simple health check response.

    Returns:
        A dict with ``alive: True`` confirming the service is running.
    """
    return {"alive": True}
