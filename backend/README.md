# uLabel — Image Labelling Platform · Backend

Backend for the image labelling platform. REST API built with FastAPI, PostgreSQL, and MinIO.

## Table of contents

- [Requirements](#requirements)
- [Getting started](#getting-started)
- [Configuration](#configuration)
- [API](#api)
- [Importing images from object storage](#importing-images-from-object-storage)
- [Sample dataset](#sample-dataset)
- [Local development](#local-development)
- [Tests](#tests)
- [Migrations](#migrations)
- [Architecture](#architecture)

---

## Requirements

- Docker and Docker Compose
- [uv](https://docs.astral.sh/uv/) (for local development without Docker)
- `wget` and `unzip` (only needed for `make seed-dataset`)

---

## Getting started

```bash
# Copy and adjust environment variables
cp .env.example .env

# Start the database, MinIO, and the application
docker compose up
```

The API will be available at `http://localhost:8000`.
The MinIO console at `http://localhost:9001` (user: `minioadmin` / `minioadmin`).

---

## Configuration

All variables are read from the `.env` file (or from the environment). See `.env.example` for the full list.

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://ulabel:secret@localhost:5432/ulabel` | PostgreSQL connection string |
| `STORAGE_ENDPOINT` | `http://localhost:9000` | Object storage URL (MinIO / S3) |
| `STORAGE_ACCESS_KEY` | `minioadmin` | Storage access key |
| `STORAGE_SECRET_KEY` | `minioadmin` | Storage secret key |
| `STORAGE_BUCKET` | `ulabel` | Bucket where images are stored |
| `IMAGE_ASSIGNMENT_TIMEOUT_SECONDS` | `1800` | Seconds before a assigned image is released back to pending |
| `IMAGE_EXPIRY_INTERVAL_SECONDS` | `300` | How often the assignment expiry task runs |

---

## API

All endpoints are prefixed with `/v1/`.

### Interactive documentation

| URL | Interface |
|---|---|
| `http://localhost:8000/docs` | Swagger UI — try endpoints directly from the browser |
| `http://localhost:8000/redoc` | ReDoc — cleaner reference view |
| `http://localhost:8000/openapi.json` | OpenAPI 3.1 schema in JSON |

### Roles

| Role | Capabilities |
|---|---|
| `admin` | Create projects, add labelers, upload and import images |
| `labeler` | View their projects, fetch images to label |

---

### Authentication — `/v1/token`

#### `POST /v1/token` — Sign in

Authenticates a user by username and returns their session information.

**Request**
```json
{ "username": "john_doe" }
```

**Response `200`**
```json
{
  "username": "john_doe",
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "role": "admin"
}
```

| Code | Description |
|---|---|
| `200` | Sign-in successful. Returns the user's `id` and `role`. |
| `404` | User not found. |

---

### Projects — `/v1/projects`

#### `POST /v1/projects` — Create project

Creates a new project. The `owner_id` must belong to a user with the `admin` role.

**Request**
```json
{
  "owner_id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Vehicle classification",
  "description": "Annotate urban traffic images indicating the type of vehicle.",
  "labels": ["car", "truck", "motorcycle", "bicycle"]
}
```

**Response `201`**
```json
{
  "id": "789e0123-e89b-12d3-a456-426614174002",
  "owner_id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Vehicle classification",
  "description": "Annotate urban traffic images indicating the type of vehicle.",
  "labels": ["car", "truck", "motorcycle", "bicycle"]
}
```

| Code | Description |
|---|---|
| `201` | Project created. |
| `403` | The `owner_id` does not have the `admin` role. |
| `404` | No user found with that `owner_id`. |

---

#### `POST /v1/projects/{project_id}/labelers` — Add labeler to project

Assigns a user with the `labeler` role to a project. From that point on they can request pending images.

**Path params:** `project_id` (UUID)

**Request**
```json
{ "labeler_id": "456e7890-e89b-12d3-a456-426614174001" }
```

**Response `200`** — updated project (same schema as `POST /v1/projects`)

| Code | Description |
|---|---|
| `200` | Labeler added. |
| `403` | The user does not have the `labeler` role. |
| `404` | Project or labeler not found. |

---

### Images — `/v1/projects/{project_id}/images`

#### `POST /v1/projects/{project_id}/images` — Register image by storage key

Registers an image that **already exists** in the bucket into the project. Useful when images are uploaded to the storage externally.

**Path params:** `project_id` (UUID)

**Request**
```json
{ "storage_key": "raw/image001.jpg" }
```

**Response `201`**
```json
{
  "id": "abc12345-e89b-12d3-a456-426614174003",
  "project_id": "789e0123-e89b-12d3-a456-426614174002",
  "storage_key": "raw/image001.jpg",
  "status": "pending"
}
```

| Code | Description |
|---|---|
| `201` | Image registered with status `pending`. |
| `404` | Project not found. |

---

#### `POST /v1/projects/{project_id}/images/upload` — Upload image directly

Uploads an image file to the bucket and registers it in the project in a single step.

**Path params:** `project_id` (UUID)

**Request** — `multipart/form-data`, field name `file`

```
POST /v1/projects/{project_id}/images/upload
Content-Type: multipart/form-data

file=<binary>
```

**Response `201`** — same schema as the endpoint above, with an auto-generated `storage_key` (`{project_id}/{image_id}`).

| Code | Description |
|---|---|
| `201` | Image uploaded and registered with status `pending`. |
| `404` | Project not found. |

---

#### `POST /v1/projects/{project_id}/images/import` — Bulk import from storage

Starts an **asynchronous** job that lists all objects in the bucket under a given prefix and registers them as project images. The response is returned immediately; use the `import_id` to poll for progress.

**Path params:** `project_id` (UUID)

**Request**
```json
{ "prefix": "raw/batch-01/" }
```

**Response `202`**
```json
{
  "import_id": "fed54321-e89b-12d3-a456-426614174005",
  "project_id": "789e0123-e89b-12d3-a456-426614174002",
  "prefix": "raw/batch-01/",
  "status": "running",
  "imported": 0,
  "error": null
}
```

| Code | Description |
|---|---|
| `202` | Import job started. |
| `404` | Project not found. |

---

#### `GET /v1/projects/{project_id}/images/imports/{import_id}` — Import job status

Returns the current state of a previously started import job.

**Path params:** `project_id` (UUID), `import_id` (UUID)

**Response `200`**
```json
{
  "import_id": "fed54321-e89b-12d3-a456-426614174005",
  "project_id": "789e0123-e89b-12d3-a456-426614174002",
  "prefix": "raw/batch-01/",
  "status": "done",
  "imported": 250,
  "error": null
}
```

`status` values: `running` · `done` · `failed`. When `status` is `failed`, the `error` field contains the error message.

| Code | Description |
|---|---|
| `200` | Current job state. |
| `404` | Job not found or does not belong to the given project. |

---

#### `GET /v1/projects/{project_id}/images/next` — Get next pending image

Assigns and returns the next `pending` image in the project to the given labeler. Includes a **presigned URL** valid for 30 minutes for direct browser/client access.

If the labeler does not finish within that time, the image is automatically reset to `pending` and becomes available again.

**Path params:** `project_id` (UUID)

**Query params:**

| Parameter | Type | Description |
|---|---|---|
| `labeler_id` | UUID | ID of the labeler requesting the image |

**Response `200`**
```json
{
  "id": "abc12345-e89b-12d3-a456-426614174003",
  "project_id": "789e0123-e89b-12d3-a456-426614174002",
  "status": "in_progress",
  "assignment_id": "def67890-e89b-12d3-a456-426614174004",
  "presigned_url": "https://storage.example.com/ulabel/...?X-Amz-Expires=1800&...",
  "presigned_url_expires_in": 1800
}
```

| Code | Description |
|---|---|
| `200` | Image assigned with presigned URL. |
| `204` | No pending images available at this time. |
| `403` | The labeler is not assigned to this project. |
| `404` | Project not found. |

---

### Labelers — `/v1/labelers`

#### `GET /v1/labelers/{labeler_id}/projects` — List labeler projects

Returns all projects the labeler is assigned to, including the available labels for each one.

**Path params:** `labeler_id` (UUID)

**Response `200`** — array of projects
```json
[
  {
    "id": "789e0123-e89b-12d3-a456-426614174002",
    "owner_id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Vehicle classification",
    "description": "Annotate urban traffic images.",
    "labels": ["car", "truck", "motorcycle", "bicycle"]
  }
]
```

| Code | Description |
|---|---|
| `200` | List of assigned projects. May be an empty array `[]`. |
| `403` | The user does not have the `labeler` role. |
| `404` | Labeler not found. |

---

## Importing images from object storage

When images already exist in object storage, they can be registered in bulk via the import endpoint instead of uploading them one by one.

**1. Start the import**

```http
POST /v1/projects/{project_id}/images/import
Content-Type: application/json

{ "prefix": "datasets/train/" }
```

Response `202 Accepted`:

```json
{
  "import_id": "550e8400-e29b-41d4-a716-446655440000",
  "project_id": "...",
  "prefix": "datasets/train/",
  "status": "running",
  "imported": 0
}
```

The job runs in the background: it lists all objects under the given prefix and inserts them into the database in batches of 1,000 rows. The operation is idempotent — re-importing the same prefix does not create duplicates.

**2. Poll for status**

```http
GET /v1/projects/{project_id}/images/imports/{import_id}
```

```json
{
  "import_id": "550e8400-e29b-41d4-a716-446655440000",
  "project_id": "...",
  "prefix": "datasets/train/",
  "status": "done",
  "imported": 12500,
  "error": null
}
```

Possible `status` values: `running` · `done` · `failed`.

---

## Sample dataset

To load the public *Dogs vs. Cats* dataset into MinIO for testing the import flow:

```bash
# Requires MinIO to be running (docker compose up -d storage)
make seed-dataset
```

This target downloads `dogs-vs-cats.zip` from HuggingFace, extracts the inner archives (`train.zip` and `test1.zip`), and uploads all images to MinIO under the `datasets/` prefix, preserving the directory structure:

```
ulabel/
└── datasets/
    ├── train/
    │   ├── cat.0.jpg
    │   ├── dog.0.jpg
    │   └── ...
    └── test1/
        ├── 1.jpg
        └── ...
```

Once uploaded, register the images in a project:

```bash
# Import the training set into an existing project
curl -X POST http://localhost:8000/v1/projects/{project_id}/images/import \
  -H "Content-Type: application/json" \
  -d '{"prefix": "datasets/train/"}'
```

---

## Local development

```bash
# Install dependencies (creates .venv automatically)
make install

# Start only the infrastructure services
docker compose up -d db storage

# Start the server with hot reload
make dev
```

### Available commands

```
make help
```

| Command | Description |
|---|---|
| `make install` | Install dependencies into `.venv` |
| `make dev` | Local server with hot reload |
| `make test` | Unit and API tests |
| `make test-integration` | Integration tests (requires a real database) |
| `make format` | Format code with ruff |
| `make lint` | Lint with ruff |
| `make typecheck` | Type-check with mypy |
| `make check` | Run format + lint + typecheck + test |
| `make build` | Build the production Docker image |
| `make migrate` | Apply pending migrations |
| `make seed-dataset` | Download and upload the Dogs vs. Cats dataset to MinIO |

---

## Tests

```bash
# Unit and API tests (no external infrastructure required)
make test

# Integration tests (requires PostgreSQL)
TEST_DATABASE_URL=postgresql+asyncpg://ulabel:secret@localhost:5432/ulabel \
  make test-integration
```

API tests use in-memory repositories and a `FakeStorageService`, so they do not require Docker or a real database.

---

## Migrations

```bash
# Apply all pending migrations
make migrate

# Create a new migration (auto-generated from the models)
make migrate-create msg="add index on images status"

# Roll back the last migration
make migrate-down
```

---

## Architecture

The project follows a layered architecture (Domain-Driven Design):

```
src/ulabel/
├── api/            # HTTP layer: FastAPI routers and Pydantic schemas
├── application/    # Use cases: orchestrate domain and infrastructure
├── domain/         # Domain models and ports (interfaces)
│   └── ports/      # Contracts: ImageRepository, StorageService, …
└── infrastructure/ # Implementations: SQLAlchemy, MinIO, in-memory repositories
```

**Image assignment flow:**

```
Admin                         Labeler
  │                              │
  ├─ POST /images/import ──────► background task
  │   lists storage objects      │
  │   inserts in DB in chunks ◄──┘
  │
  │                         GET /images/next
  │                              ├─ assigns image (status → in_progress)
  │                              └─ returns presigned URL (30 min)
  │
  │         (if not labelled within 30 min)
  │         periodic task releases image (status → pending)
```

**Technology stack:**

| Layer | Technology |
|---|---|
| Web framework | FastAPI + Uvicorn |
| ORM | SQLAlchemy 2 (async) + asyncpg |
| Migrations | Alembic |
| Object storage | MinIO (S3-compatible) |
| Dependency injection | dependency-injector |
| Packaging | uv + hatchling |
| Code quality | ruff + mypy + pre-commit |
