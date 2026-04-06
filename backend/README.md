# uLabel — Image Labelling Platform · Backend

Backend for the image labelling platform. REST API built with FastAPI, PostgreSQL, and MinIO.

## Table of contents

- [Requirements](#requirements)
- [Getting started](#getting-started)
- [Configuration](#configuration)
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

---

## Getting started

```bash
# Copy and adjust environment variables
cp .env.example .env

# Build the dev Docker image
make setup

# Start the database, MinIO, and the application
docker compose up
```

The API will be available at `http://localhost:8000`.
The MinIO console at `http://localhost:9001` (user: `minioadmin` / `minioadmin`).

Interactive API documentation:

| URL | Interface |
|---|---|
| `http://localhost:8000/docs` | Swagger UI — try endpoints directly from the browser |
| `http://localhost:8000/redoc` | ReDoc — cleaner reference view |
| `http://localhost:8000/openapi.json` | OpenAPI 3.1 schema in JSON |

---

## Configuration

Configuration is split between two files:

- **`.env`** — secrets and environment-specific overrides (gitignored). See `.env.example` for the full list.
- **`config.yml`** — non-secret settings with `${ENV_VAR}` interpolation for values that come from `.env`.

### Environment variables (`.env`)

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://ulabel:secret@localhost:5432/ulabel` | PostgreSQL connection string |
| `TEST_DATABASE_URL` | same as `DATABASE_URL` | Connection string used by integration tests |
| `STORAGE_ACCESS_KEY` | `minioadmin` | Object storage access key |
| `STORAGE_SECRET_KEY` | `minioadmin` | Object storage secret key |
| `STORAGE_ENDPOINT` | `localhost:9000` | Object storage endpoint (overrides `config.yml`) |
| `STORAGE_PUBLIC_ENDPOINT` | _(empty)_ | Public-facing storage URL for presigned URLs |
| `OTEL_TRACING_ENABLED` | `false` | Enable OpenTelemetry distributed tracing |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4317` | OTLP gRPC endpoint (Tempo) |
| `OTEL_TRACES_SAMPLE_RATIO` | `1.0` | Tracing sample ratio (`0.0`–`1.0`) |
| `OTEL_METRICS_ENABLED` | `false` | Enable Prometheus metrics collection |
| `LOG_LEVEL` | `INFO` | Logging level |

### Application config (`config.yml`)

| Key | Default | Description |
|---|---|---|
| `database.pool_size` | `10` | Connection pool size |
| `database.max_overflow` | `20` | Extra connections allowed beyond pool size |
| `database.pool_recycle` | `3600` | Seconds before a connection is recycled |
| `storage.bucket` | `ulabel` | Bucket where images are stored |
| `storage.presigned_url_expiry_seconds` | `3600` | Presigned URL lifetime (seconds) |
| `tasks.image_assignment_timeout_seconds` | `60` | Seconds before an assigned image is released back to `pending` |
| `tasks.image_expiry_interval_seconds` | `30` | How often the assignment expiry task runs (seconds) |

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
# Build the dev Docker image (required once)
make setup

# Install dependencies into local .venv (for IDE support)
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
| `make setup` | Build the dev Docker image |
| `make install` | Sync all dependencies (including dev) into local `.venv` |
| `make pre-commit-install` | Install pre-commit hooks into `.git/hooks` |
| `make dev` | Start dev server with hot reload |
| `make shell` | Open an interactive shell inside the dev container |
| `make test-unit` | Run unit tests |
| `make test-cov` | Run all tests with coverage report |
| `make test-integration` | Integration tests (requires `TEST_DATABASE_URL`) |
| `make test-e2e` | E2E API tests (requires `TEST_DATABASE_URL`) |
| `make format` | Format code with ruff |
| `make lint` | Lint with ruff |
| `make lint-fix` | Lint and auto-fix with ruff |
| `make typecheck` | Type-check with mypy |
| `make check` | Run format + lint + typecheck + test |
| `make build` | Build the production Docker image |
| `make run` | Start the app with docker compose |
| `make migrate` | Apply pending migrations |
| `make migrate-create msg="..."` | Create a new auto-generated migration |
| `make migrate-down` | Roll back the last migration |
| `make seed-dataset` | Download and upload the Dogs vs. Cats dataset to MinIO |
| `make docs` | Serve documentation locally with hot reload |
| `make docs-build` | Build documentation as a static site |

All commands run inside Docker containers — no local Python installation is required beyond IDE support.

---

## Tests

```bash
# Unit tests (no external infrastructure required)
make test-unit

# Integration tests (requires a running PostgreSQL instance)
TEST_DATABASE_URL=postgresql+asyncpg://ulabel:secret@localhost:5432/ulabel \
  make test-integration

# E2E API tests (requires a running PostgreSQL instance)
TEST_DATABASE_URL=postgresql+asyncpg://ulabel:secret@localhost:5432/ulabel \
  make test-e2e

# All tests with coverage report
make test-cov
```

Unit and API tests use in-memory repositories and a `FakeStorageService`, so they do not require a real database or object storage.

E2E tests exercise full API workflows (HTTP → use case → database) with a real PostgreSQL and `FakeStorageService`.

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
├── infrastructure/ # Implementations: SQLAlchemy, MinIO, in-memory repositories
│   └── observability/  # Tracing, logging, and metrics (OpenTelemetry)
└── container.py    # Dependency injection (dependency-injector)
```

**Image assignment flow:**

```mermaid
sequenceDiagram
    actor Admin
    participant API
    participant DB
    participant Storage
    actor Labeler

    Admin->>API: POST /images/import {prefix}
    API-->>Admin: 202 Accepted (import_id)
    API->>Storage: List objects under prefix
    Storage-->>API: Object keys
    API->>DB: Insert images in batches (status: pending)

    Labeler->>API: GET /images/next?labeler_id=...
    API->>DB: Assign next pending image (status → in_progress)
    API->>Storage: Generate presigned URL (1 h)
    Storage-->>API: Presigned URL
    API-->>Labeler: Image + presigned URL

    Note over API,DB: If not labelled within timeout
    API->>DB: Release image (status → pending)
```

**Technology stack:**

| Layer | Technology |
|---|---|
| Web framework | FastAPI + Uvicorn |
| ORM | SQLAlchemy 2 (async) + asyncpg |
| Migrations | Alembic |
| Object storage | MinIO (S3-compatible) via aioboto3 |
| Dependency injection | dependency-injector |
| Observability | OpenTelemetry + Prometheus + Grafana + Loki + Tempo |
| Documentation | MkDocs (Material theme) |
| Packaging | uv + hatchling |
| Code quality | ruff + mypy + pre-commit |
