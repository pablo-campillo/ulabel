import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from ulabel.api.api import api_router
from ulabel.api.error_handlers import domain_error_handler
from ulabel.container import Container
from ulabel.domain.errors import DomainError

container = Container()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await container.storage_service().ensure_bucket()
    task = asyncio.create_task(container.expire_images_task().run())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="uLabel API",
    description="""
API for managing image labelling projects.

## Workflow

1. **Authentication** — the user calls `POST /v1/token` with their username and receives their ID and role.
2. **Admin** creates projects (`POST /v1/projects`) and adds labelers (`POST /v1/projects/{id}/labelers`).
3. **Image loading** — the admin uploads images one by one (`POST /v1/projects/{id}/images/upload`), registers them by storage key (`POST /v1/projects/{id}/images`), or bulk-imports from the bucket (`POST /v1/projects/{id}/images/import`).
4. **Labelling** — the labeler creates an assignment (`POST /v1/projects/{id}/assignments`), which returns the next pending image with a presigned URL valid for 30 minutes. If not completed in time, the assignment expires and the image becomes available again.

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
app.add_exception_handler(DomainError, domain_error_handler)

app.include_router(api_router, prefix="/v1")


@app.get("/", tags=["Health"], summary="Health check", description="Verifies the service is up and running.")
async def root():
    return {"alive": True}
