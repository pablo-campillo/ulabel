# API Design

uLabel exposes a REST API built with FastAPI. This page explains the endpoint design, schema conventions, error handling strategy, and middleware architecture.

## Endpoint Map

All endpoints live under the `/v1` prefix.

### Authentication

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/v1/token` | Sign in by username, returns a `Claim` with user ID and role |

### Projects

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/v1/projects` | List projects with pagination and optional name filter |
| `POST` | `/v1/projects` | Create a new labeling project (admin only) |
| `PATCH` | `/v1/projects/{project_id}` | Update project name, description, or labelers |
| `POST` | `/v1/projects/{project_id}/labelers` | Add a labeler to a project |

### Images & Labeling

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/v1/projects/{project_id}/images` | Register an existing storage object as a project image |
| `POST` | `/v1/projects/{project_id}/images/upload` | Upload an image file directly |
| `POST` | `/v1/projects/{project_id}/images/import` | Start async bulk import from a storage prefix |
| `GET` | `/v1/projects/{project_id}/images/imports/{import_id}` | Poll bulk import job status |
| `POST` | `/v1/projects/{project_id}/images/{image_id}/label` | Submit a label for an assigned image |

### Assignments

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/v1/projects/{project_id}/assignments` | Get next pending image with a presigned URL (30-min expiry) |

### Exports

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/v1/projects/{project_id}/export` | Export labels as JSON or CSV (redirects to presigned URL) |

### Statistics

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/v1/projects/{project_id}/stats` | Get project statistics (counts, distribution, daily activity) |

### Labelers

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/v1/labelers/autocomplete` | Search labelers by username prefix |
| `GET` | `/v1/labelers/{labeler_id}/projects` | List projects assigned to a labeler |

## Schema Design

### Request and Response Separation

Every endpoint has distinct request and response schemas. This keeps the API contract explicit and avoids leaking internal fields:

```python
class CreateProjectRequest(BaseModel):
    owner_id: UUID
    name: str
    description: str
    labels: set[str]

class ProjectResponse(BaseModel):
    id: UUID
    owner_id: UUID
    name: str
    description: str
    labels: set[str]
    labelers: list[LabelerInfo]
    created_at: datetime | None
```

### Generic Pagination

Paginated list endpoints use a generic wrapper:

```python
class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int
```

This is reused for project listing and any future paginated resource. Query parameters `limit` and `offset` control pagination, with an optional `name` filter for search.

### Pydantic v2 with orjson

All schemas use Pydantic v2 `BaseModel` with `model_config = ConfigDict(from_attributes=True)` where needed. FastAPI is configured with `orjson` for high-performance JSON serialization, which is particularly beneficial for large export payloads and statistics responses.

## Error Handling

### Domain Error Mapping

A single global exception handler maps every `DomainError` subclass to its HTTP response:

| Domain Error | HTTP Status | Code |
|---|---|---|
| `ProjectNotFound` | 404 | `PROJECT_NOT_FOUND` |
| `UserNotFound` | 404 | `USER_NOT_FOUND` |
| `ImageNotFound` | 404 | `IMAGE_NOT_FOUND` |
| `NoLabelsFound` | 404 | `NO_LABELS_FOUND` |
| `ImportJobNotFound` | 404 | `IMPORT_JOB_NOT_FOUND` |
| `Unauthorized` | 403 | `UNAUTHORIZED` |
| `LabelerNotInProject` | 403 | `LABELER_NOT_IN_PROJECT` |
| `LabelerMismatch` | 403 | `LABELER_MISMATCH` |
| `ProjectNameAlreadyExists` | 409 | `PROJECT_NAME_ALREADY_EXISTS` |
| `ImageNotInProgress` | 409 | `IMAGE_NOT_IN_PROGRESS` |
| `AssignmentMismatch` | 409 | `ASSIGNMENT_MISMATCH` |
| `InvalidLabel` | 422 | `INVALID_LABEL` |
| `NoImageAvailable` | 204 | *(no content)* |

### Uniform Error Response

All errors return the same JSON structure:

```json
{
  "error": {
    "code": "PROJECT_NOT_FOUND",
    "message": "Project not found",
    "details": null
  }
}
```

This makes it easy for the frontend to parse errors consistently. The handler also logs each domain error and increments the `domain_errors_total` Prometheus metric.

## Authentication Model

uLabel uses a simplified username-based authentication:

1. The frontend sends `POST /v1/token` with a username.
2. The backend looks up or creates the user and returns a `Claim` containing the user's `id`, `username`, and `role`.
3. Subsequent requests include the user ID in request bodies (e.g., `labeler_id`, `owner_id`).

Roles determine access:

- **Admin**: Create and manage projects, upload images, configure labelers.
- **Labeler**: View assigned projects, receive image assignments, submit labels.

Authorization is enforced at the use case level — routers pass the user ID, and use cases validate permissions against the domain (e.g., checking that a labeler belongs to the project).

## Middleware

### Prometheus Metrics

The `PrometheusMiddleware` wraps every request and collects:

- **`http_requests_total`** — Counter by method, path template, and status code.
- **`http_request_duration_seconds`** — Histogram with buckets from 5ms to 10s.
- **`http_requests_in_progress`** — Gauge for concurrent requests.
- **`http_exceptions_total`** — Counter for unhandled exceptions.

Path labels use **route templates** (`/v1/projects/{project_id}/images`) rather than actual URLs to prevent cardinality explosion from UUIDs.

Each metric observation includes an **exemplar** linking to the current trace ID, enabling one-click navigation from a Grafana metric panel to the corresponding trace in Tempo.

### Versioning

The API uses a `/v1` prefix on all routes, applied by mounting the feature routers under a versioned `APIRouter`. This allows future breaking changes to coexist under `/v2` without disrupting existing clients.

## Router Organization

Routers are organized by domain resource:

```
api/routers/
├── tokens.py        # Authentication
├── projects.py      # Project CRUD + labeler management
├── images.py        # Image upload, import, label submission
├── assignments.py   # Image assignment to labelers
├── exports.py       # Label data export
├── stats.py         # Project statistics
└── labelers.py      # Labeler search and project listing
```

Each router is a FastAPI `APIRouter` with appropriate `prefix` and `tags`. They are aggregated in `api.py` and mounted on the main app in `main.py`.

## Dependency Injection in Routers

Route handlers receive use cases via `dependency-injector`'s `@inject` decorator:

```python
@router.post("/{project_id}/assignments")
@inject
async def create_assignment(
    project_id: UUID,
    body: CreateAssignmentRequest,
    use_case: CreateAssignmentUseCase = Depends(
        Provide[Container.create_assignment_use_case]
    ),
    storage: StorageService = Depends(Provide[Container.storage_service]),
):
    image = await use_case.execute(project_id, body.labeler_id)
    ...
```

This keeps handlers thin — they parse HTTP, call the use case, and format the response. All business logic lives in the application layer.
