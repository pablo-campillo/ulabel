# uLabel API Documentation

Welcome to the **uLabel** documentation — a backend API for an image labeling and annotation platform.

## Overview

uLabel provides a REST API built with FastAPI that enables:

- **Project management**: Create and configure labeling projects with custom categories.
- **Image handling**: Upload, import from S3/MinIO storage, and manage images within projects.
- **Labeling workflow**: Assign images to labelers and collect annotations.
- **Export**: Export labeled data for downstream use.
- **Observability**: Built-in tracing, metrics, and structured logging via OpenTelemetry.

## Documentation Structure

This documentation follows the [Diataxis](https://diataxis.fr/) framework:

| Section | Purpose |
|---|---|
| [Tutorials](tutorials/getting-started.md) | Step-by-step guides to get started |
| [How-To Guides](how-to-guides.md) | Recipes for common tasks |
| [Reference](reference/index.md) | Auto-generated API reference from source code |
| [Explanation](explanation/architecture.md) | Background and architecture decisions |

## Quick Start

```bash
# Install dependencies
uv sync

# Run the API
make run
```

See the [Getting Started](tutorials/getting-started.md) tutorial for a complete walkthrough.
