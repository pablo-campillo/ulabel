# Getting Started

This tutorial walks you through setting up and running the uLabel backend API.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- PostgreSQL database
- S3-compatible object storage (e.g., MinIO)

## Installation

Clone the repository and install dependencies:

```bash
git clone <repository-url>
cd ulabel/backend
uv sync
```

## Configuration

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Key environment variables:

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `S3_ENDPOINT` | S3/MinIO endpoint URL |
| `S3_BUCKET` | Bucket name for image storage |

## Running the API

Start the development server:

```bash
make run
```

The API will be available at `http://localhost:8000`.

## Interactive API Docs

FastAPI automatically generates interactive documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Database Migrations

Run database migrations with Alembic:

```bash
make migrate
```

## Next Steps

- Explore the [API Reference](../reference/index.md) for detailed endpoint documentation.
- Read about the [Architecture](../explanation/architecture.md) to understand the project structure.
