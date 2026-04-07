# How-To Guides

Practical recipes for common tasks with the uLabel API.

## Project Management

### Create a New Labeling Project

```bash
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "My Project", "description": "Image classification task"}'
```

### Add a Labeler to a Project

```bash
curl -X POST http://localhost:8000/api/v1/projects/{project_id}/labelers \
  -H "Content-Type: application/json" \
  -d '{"labeler_id": "labeler-uuid"}'
```

## Image Management

### Upload an Image to a Project

```bash
curl -X POST http://localhost:8000/api/v1/projects/{project_id}/images \
  -F "file=@image.jpg"
```

### Import Images from S3 Storage

```bash
curl -X POST http://localhost:8000/api/v1/projects/{project_id}/images/import \
  -H "Content-Type: application/json" \
  -d '{"prefix": "dataset/batch-1/"}'
```

## Labeling Workflow

### Create an Assignment

```bash
curl -X POST http://localhost:8000/api/v1/assignments \
  -H "Content-Type: application/json" \
  -d '{"project_id": "project-uuid", "labeler_id": "labeler-uuid"}'
```

### Submit a Label

```bash
curl -X POST http://localhost:8000/api/v1/assignments/{assignment_id}/labels \
  -H "Content-Type: application/json" \
  -d '{"category": "cat", "confidence": 0.95}'
```

## Data Export

### Export Labels

```bash
curl http://localhost:8000/api/v1/projects/{project_id}/exports
```

## Load Testing

### Run a labeling benchmark

```bash
make benchmark PROJECT_ID=<uuid>
```

Spawns one concurrent user per labeler and loops `assign → label (random)` for 60 seconds. See [Load Testing](load-testing.md) for configuration options and web UI mode.

## Observability

- [Grafana Dashboards](grafana-dashboards.md) — How to use the monitoring dashboards
- [Adding Observability](adding-observability.md) — How to add new logs, metrics, or traces
